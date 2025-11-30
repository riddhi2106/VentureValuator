# agents/financial_agent.py
"""
FinancialModelAgent (mix of C1 + C2)

Produces:
- Monthly projections (24 months)
- Annual summaries (year1, year2)
- Cost breakdown (fixed + variable)
- Gross profit series
- Net cashflow, burn, runway, breakeven
- CAC / LTV and unit economics
- 3-scenario forecast: conservative / base / optimistic
- 5-year projections (monthly + annual)
"""

from typing import Dict, Any
import re
import json
import math

from tools.finance_utils import (
    monthly_growth_series,
    cumulative,
    cac_ltv,
    monthly_to_annual,
    yearly_growth_projection,
    multi_year_financial_table
)

from tools.llm_client import call_gemini

DEFAULT_MONTHS = 24


def _parse_money_to_float(s: str):
    if not s:
        return None
    s = str(s).lower().replace(",", "").strip()
    s = s.replace("₹", "").replace("rs", "").strip()

    try:
        if "b" in s and any(ch.isdigit() for ch in s):
            num = float(re.findall(r"[\d\.]+", s)[0])
            return num * 1e9

        if "m" in s and "lakh" not in s:
            num = float(re.findall(r"[\d\.]+", s)[0])
            return num * 1e6

        if "lakh" in s or ("l" in s and re.search(r"\d+l", s)):
            num = float(re.findall(r"[\d\.]+", s)[0])
            return num * 100000

        found = re.findall(r"[\d\.]+", s)
        if found:
            return float(found[0])

    except Exception:
        return None

    return None


def _safe_div(a, b):
    try:
        return a / b if b else None
    except:
        return None


class FinancialAgent:
    def __init__(self, months: int = DEFAULT_MONTHS):
        self.months = months

    def _infer_inputs(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        inputs = {}

        lm = extracted.get("notable_metrics", {}).get("Last month revenue") or ""
        revenue_monthly = _parse_money_to_float(lm)
        if not revenue_monthly:
            revenue_monthly = 100000.0

        inputs["revenue_monthly"] = revenue_monthly

        mom = extracted.get("notable_metrics", {}).get("Month-over-month growth") or ""
        growth_monthly = 0.10
        if isinstance(mom, str) and "%" in mom:
            try:
                growth_monthly = float(mom.replace("%", "")) / 100.0
            except:
                pass
        elif isinstance(mom, (int, float)):
            growth_monthly = float(mom)

        inputs["growth_monthly"] = growth_monthly

        mau_s = extracted.get("notable_metrics", {}).get("Monthly active users") or ""
        mau = None
        if isinstance(mau_s, str):
            digits = re.findall(r"[\d,]+", mau_s.replace("+", ""))
            if digits:
                try:
                    mau = int(digits[0].replace(",", ""))
                except:
                    mau = None

        inputs["mau"] = mau

        inputs["gross_margin"] = 0.25

        cac = 150.0
        if mau and revenue_monthly:
            arpu = revenue_monthly / max(1, mau)
            cac = max(50.0, 3 * arpu)

        inputs["cac"] = cac

        inputs["churn_monthly"] = 0.05
        inputs["fixed_monthly_costs"] = 800000.0

        if mau and revenue_monthly:
            inputs["arpu_monthly"] = revenue_monthly / max(1, mau)
        else:
            inputs["arpu_monthly"] = 250.0

        return inputs

    def _build_projection(self, start_rev, growth, months, gross_margin, fixed_monthly):
        revenue_series = monthly_growth_series(start_rev, growth, months)
        gross_profit_series = [r * gross_margin for r in revenue_series]
        variable_costs = [r * (1 - gross_margin) for r in revenue_series]
        total_costs = [fixed_monthly + v for v in variable_costs]
        net_cashflow = [gp - fixed_monthly for gp in gross_profit_series]

        return {
            "revenue_series": revenue_series,
            "gross_profit_series": gross_profit_series,
            "variable_costs": variable_costs,
            "total_costs": total_costs,
            "net_cashflow": net_cashflow
        }

    def _breakeven_month(self, cumulative_net):
        for i, v in enumerate(cumulative_net):
            if v >= 0:
                return i + 1
        return None

    def run(self, extracted: Dict[str, Any], overrides: Dict[str, Any] = None) -> Dict[str, Any]:

        if overrides is None:
            overrides = {}

        inputs = self._infer_inputs(extracted)
        inputs.update(overrides)

        base_growth = inputs["growth_monthly"]
        scenarios = {
            "conservative": max(-0.02, base_growth * 0.5),
            "base": base_growth,
            "optimistic": base_growth * 1.5
        }

        months = self.months
        out = {"inputs": inputs, "months": months, "scenarios": {}}

        for name, g in scenarios.items():
            proj = self._build_projection(
                start_rev=inputs["revenue_monthly"],
                growth=g,
                months=months,
                gross_margin=inputs["gross_margin"],
                fixed_monthly=inputs["fixed_monthly_costs"]
            )

            cum_net = cumulative(proj["net_cashflow"])
            breakeven = self._breakeven_month(cum_net)
            year1 = monthly_to_annual(proj["net_cashflow"][:12])
            year2 = monthly_to_annual(proj["net_cashflow"][12:24]) if months >= 24 else None

            cac_ltv_res = cac_ltv(
                inputs["cac"],
                inputs["arpu_monthly"],
                inputs["gross_margin"],
                inputs["churn_monthly"]
            )

            out["scenarios"][name] = {
                "growth_monthly": g,
                "revenue_series": proj["revenue_series"],
                "gross_profit_series": proj["gross_profit_series"],
                "total_costs": proj["total_costs"],
                "net_cashflow": proj["net_cashflow"],
                "cumulative_net_cashflow": cum_net,
                "breakeven_month": breakeven,
                "yearly_net": {"year1": year1, "year2": year2},
                "cac_ltv": cac_ltv_res
            }

        out["summary"] = {
            "revenue_monthly_start": inputs["revenue_monthly"],
            "arpu_monthly": inputs["arpu_monthly"],
            "cac": inputs["cac"],
            "gross_margin": inputs["gross_margin"]
        }

        # ⭐ 5-Year Projection (60 months)
        five_year = multi_year_financial_table(
            start_monthly_revenue=inputs["revenue_monthly"],
            monthly_growth=inputs["growth_monthly"],
            months=60
        )

        out["five_year_projection"] = {
            "annual_revenue": five_year["annual"],
            "monthly_revenue": five_year["monthly"]
        }

        if overrides.get("explain", False):
            try:
                prompt = (
                    "Explain these financial projections succinctly.\n\n"
                    f"INPUTS:\n{json.dumps(inputs, indent=2)}\n\n"
                    f"SCENARIOS:\n{json.dumps(list(out['scenarios'].keys()), indent=2)}"
                )
                out["llm_explanation"] = call_gemini(prompt)
            except Exception as e:
                out["llm_explanation_error"] = str(e)

        return out
