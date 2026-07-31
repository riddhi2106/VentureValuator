# agents/financial_agent.py
"""Deterministic financial modeling for an extracted startup pitch deck.

The agent deliberately keeps its formulas transparent and separates every input
into ``deck``, ``derived``, or ``assumption`` provenance. It produces a 24-month
cash-flow model, conservative/base/optimistic scenarios, simple CAC/LTV unit
economics, breakeven timing, and a five-year revenue-only view.

This is a diligence aid rather than audited financial advice. Defaults make it
possible to model incomplete decks, but downstream scoring discounts results
that depend on those assumptions.
"""

import json
import re
from typing import Any, Dict

from tools.finance_utils import (
    cac_ltv,
    cumulative,
    monthly_growth_series,
    monthly_to_annual,
    multi_year_financial_table,
)
from tools.llm_client import call_llm

DEFAULT_MONTHS = 24
LONG_RANGE_MONTHS = 60

# Centralizing fallbacks makes the behavior of sparse decks auditable. These
# defaults are intentionally tagged as assumptions and never presented as facts.
ASSUMED_MONTHLY_REVENUE = 100_000.0
ASSUMED_MONTHLY_GROWTH = 0.10
ASSUMED_GROSS_MARGIN = 0.25
ASSUMED_CAC = 150.0
ASSUMED_MONTHLY_CHURN = 0.05
ASSUMED_FIXED_MONTHLY_COSTS = 800_000.0
ASSUMED_MONTHLY_ARPU = 250.0

CONSERVATIVE_GROWTH_FACTOR = 0.5
OPTIMISTIC_GROWTH_FACTOR = 1.5
MAX_CONSERVATIVE_CONTRACTION = -0.02
MAX_MODELED_MONTHLY_GROWTH = 1.0
OVERRIDABLE_INPUTS = {
    "revenue_monthly",
    "growth_monthly",
    "gross_margin",
    "cac",
    "churn_monthly",
    "fixed_monthly_costs",
    "arpu_monthly",
}


def _parse_money_to_float(s: str) -> float | None:
    """Parse common Western and Indian magnitude suffixes into a float.

    Currency symbols are ignored because the deck's native currency is preserved
    at the presentation layer. Supported magnitude examples include ``$1.5m``,
    ``3b``, and ``₹2 lakh``. ``None`` is returned when no numeric value can be
    extracted, allowing the caller to record a documented assumption instead.
    """

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

    except (IndexError, ValueError):
        return None

    return None


def _safe_div(a, b):
    """Divide two values, returning ``None`` for invalid or zero denominators.

    The helper is retained for callers that need a missing-value signal instead
    of an exception while processing inconsistent pitch-deck metrics.
    """

    try:
        return a / b if b else None
    except (TypeError, ZeroDivisionError):
        return None


def _get_metric(metrics: dict, *keys):
    """Return the first non-empty metric across known deck aliases.

    Extraction prompts and source decks use inconsistent capitalization and
    labels. Alias lookup keeps that normalization concern out of the formulas.
    """

    for k in keys:
        val = metrics.get(k)
        if val not in (None, "", []):
            return val
    return ""


class FinancialAgent:
    """Build transparent scenario projections from extracted pitch-deck metrics.

    Args:
        months: Positive projection horizon for detailed cash-flow scenarios.

    The five-year revenue view always uses ``LONG_RANGE_MONTHS`` because it is a
    separate, explicitly more speculative output.
    """

    def __init__(self, months: int = DEFAULT_MONTHS):
        """Configure the scenario-model horizon in months."""

        if months <= 0:
            raise ValueError("months must be positive")
        self.months = months

    def _infer_inputs(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize deck metrics and record whether each value is sourced or assumed.

        Source provenance is retained in ``_sources`` because downstream scoring
        discounts attractive unit economics when their inputs were not evidenced
        by the uploaded deck.
        """

        inputs = {}
        sources = {}

        metrics = extracted.get("notable_metrics", {}) or {}
        lm = _get_metric(
            metrics,
            "revenue_last_month",
            "Last month revenue",
            "last_month_revenue",
            "revenue (last month)",
        )
        revenue_monthly = _parse_money_to_float(lm)
        if not revenue_monthly:
            revenue_monthly = ASSUMED_MONTHLY_REVENUE
            sources["revenue_monthly"] = "assumption"
        else:
            sources["revenue_monthly"] = "deck"

        inputs["revenue_monthly"] = revenue_monthly

        mom = _get_metric(
            metrics,
            "mom_growth",
            "Month-over-month growth",
            "MoM growth",
            "month-over-month growth",
        )
        growth_monthly = ASSUMED_MONTHLY_GROWTH
        sources["growth_monthly"] = "assumption"
        if isinstance(mom, str) and "%" in mom:
            try:
                growth_monthly = float(mom.replace("%", "")) / 100.0
                sources["growth_monthly"] = "deck"
            except (TypeError, ValueError):
                pass
        elif isinstance(mom, (int, float)):
            growth_monthly = float(mom)
            sources["growth_monthly"] = "deck"

        inputs["growth_monthly"] = growth_monthly

        mau_s = _get_metric(metrics, "mau", "Monthly active users", "MAU")
        mau = None
        if isinstance(mau_s, str):
            digits = re.findall(r"[\d,]+", mau_s.replace("+", ""))
            if digits:
                try:
                    mau = int(digits[0].replace(",", ""))
                except (TypeError, ValueError):
                    mau = None

        inputs["mau"] = mau

        gross_margin_raw = _get_metric(
            metrics,
            "gross_margin",
            "Gross margin",
            "average_gross_margin",
        )
        gross_margin = _parse_money_to_float(gross_margin_raw)
        if gross_margin is not None:
            gross_margin = gross_margin / 100 if gross_margin > 1 else gross_margin
            sources["gross_margin"] = "deck"
        else:
            gross_margin = ASSUMED_GROSS_MARGIN
            sources["gross_margin"] = "assumption"
        inputs["gross_margin"] = gross_margin

        cac_raw = _get_metric(metrics, "cac", "CAC", "customer_acquisition_cost")
        cac = _parse_money_to_float(cac_raw)
        if cac is not None:
            sources["cac"] = "deck"
        elif mau and sources["revenue_monthly"] == "deck":
            arpu = revenue_monthly / max(1, mau)
            # Without stated CAC, three months of derived ARPU is a simple
            # payback-period proxy. The floor avoids implausibly tiny CAC values.
            cac = max(50.0, 3 * arpu)
            sources["cac"] = "derived"
        else:
            cac = ASSUMED_CAC
            sources["cac"] = "assumption"

        inputs["cac"] = cac

        churn_raw = _get_metric(metrics, "churn_monthly", "monthly_churn", "churn")
        churn = _parse_money_to_float(churn_raw)
        if churn is not None:
            churn = churn / 100 if churn > 1 else churn
            sources["churn_monthly"] = "deck"
        else:
            churn = ASSUMED_MONTHLY_CHURN
            sources["churn_monthly"] = "assumption"
        inputs["churn_monthly"] = churn

        fixed_cost_raw = _get_metric(
            metrics,
            "fixed_monthly_costs",
            "monthly_operating_costs",
            "burn_monthly",
        )
        fixed_costs = _parse_money_to_float(fixed_cost_raw)
        if fixed_costs is not None:
            sources["fixed_monthly_costs"] = "deck"
        else:
            fixed_costs = ASSUMED_FIXED_MONTHLY_COSTS
            sources["fixed_monthly_costs"] = "assumption"
        inputs["fixed_monthly_costs"] = fixed_costs

        if mau and revenue_monthly:
            inputs["arpu_monthly"] = revenue_monthly / max(1, mau)
            sources["arpu_monthly"] = "derived"
        else:
            inputs["arpu_monthly"] = ASSUMED_MONTHLY_ARPU
            sources["arpu_monthly"] = "assumption"

        inputs["_sources"] = sources
        return inputs

    def _build_projection(self, start_rev, growth, months, gross_margin, fixed_monthly):
        """Build revenue, cost, and cash-flow series for one growth scenario.

        Variable costs are the non-gross-margin share of revenue. Net cash flow
        therefore simplifies to gross profit less fixed operating costs.

        Returns:
            Parallel monthly arrays for revenue, gross profit, variable costs,
            total costs, and net cash flow. All arrays have ``months`` entries.
        """

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
            "net_cashflow": net_cashflow,
        }

    def _apply_overrides(self, inputs: dict, overrides: dict, warnings: list[str]) -> None:
        """Apply only supported sensitivity inputs and preserve their provenance."""

        for key, value in overrides.items():
            if key == "explain":
                continue
            if key not in OVERRIDABLE_INPUTS:
                warnings.append(f"Ignored unsupported financial override: {key}")
                continue
            inputs[key] = value
            inputs["_sources"][key] = "override"

    def _sanitize_inputs(self, inputs: dict, warnings: list[str]) -> None:
        """Replace impossible financial values and bound unstable projections.

        Invalid deck values fall back to documented assumptions and lose
        deck-sourced provenance. Monthly growth above 100% is retained as a
        reported claim in extraction but capped in the compounding model to
        avoid meaningless five-year overflow.
        """

        defaults = {
            "revenue_monthly": ASSUMED_MONTHLY_REVENUE,
            "gross_margin": ASSUMED_GROSS_MARGIN,
            "cac": ASSUMED_CAC,
            "churn_monthly": ASSUMED_MONTHLY_CHURN,
            "fixed_monthly_costs": ASSUMED_FIXED_MONTHLY_COSTS,
            "arpu_monthly": ASSUMED_MONTHLY_ARPU,
        }
        bounds = {
            "revenue_monthly": (0, None),
            "gross_margin": (0, 1),
            "cac": (0, None),
            "churn_monthly": (0, 1),
            "fixed_monthly_costs": (0, None),
            "arpu_monthly": (0, None),
        }

        for key, (minimum, maximum) in bounds.items():
            try:
                value = float(inputs[key])
            except (KeyError, TypeError, ValueError):
                value = defaults[key]
                valid = False
            else:
                valid = value >= minimum and (maximum is None or value <= maximum)
                if key == "churn_monthly" and value == 0:
                    valid = False

            if not valid:
                warnings.append(
                    f"Invalid {key} value was replaced with a documented assumption"
                )
                inputs[key] = defaults[key]
                inputs["_sources"][key] = "assumption"
            else:
                inputs[key] = value

        try:
            growth = float(inputs["growth_monthly"])
        except (KeyError, TypeError, ValueError):
            growth = ASSUMED_MONTHLY_GROWTH
            inputs["_sources"]["growth_monthly"] = "assumption"
            warnings.append("Invalid growth_monthly value was replaced with an assumption")

        if growth <= -1:
            growth = ASSUMED_MONTHLY_GROWTH
            inputs["_sources"]["growth_monthly"] = "assumption"
            warnings.append("Growth at or below -100% was replaced with an assumption")
        elif growth > MAX_MODELED_MONTHLY_GROWTH:
            growth = MAX_MODELED_MONTHLY_GROWTH
            source = inputs["_sources"].get("growth_monthly", "assumption")
            inputs["_sources"]["growth_monthly"] = f"bounded_{source}"
            warnings.append("Monthly growth was capped at 100% for projection stability")
        inputs["growth_monthly"] = growth

    def _breakeven_month(self, cumulative_net):
        """Return the first one-based month with non-negative cumulative cash flow.

        ``None`` means the scenario never recovers its accumulated losses inside
        the configured horizon. One-based indexing matches labels shown in the UI.
        """

        for i, v in enumerate(cumulative_net):
            if v >= 0:
                return i + 1
        return None

    def run(self, extracted: Dict[str, Any], overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate three scenarios, unit economics, and a five-year revenue view.

        Overrides are applied after inference so callers can run explicit
        sensitivities without losing the original source-provenance map.

        Args:
            extracted: Structured output from ``ExtractionAgent``.
            overrides: Optional normalized values such as ``growth_monthly`` or
                ``fixed_monthly_costs``. Setting ``explain`` requests an LLM
                narrative without changing any deterministic calculations.

        Returns:
            A JSON-serializable model containing inputs, source provenance,
            detailed scenarios, a summary, and the long-range revenue projection.
        """

        if overrides is None:
            overrides = {}

        inputs = self._infer_inputs(extracted)
        warnings: list[str] = []
        self._apply_overrides(inputs, overrides, warnings)
        self._sanitize_inputs(inputs, warnings)

        base_growth = inputs["growth_monthly"]
        scenarios = {
            # Bound the downside case at -2% monthly contraction so sparse decks
            # do not produce an implausibly catastrophic default forecast.
            "conservative": max(
                MAX_CONSERVATIVE_CONTRACTION,
                base_growth * CONSERVATIVE_GROWTH_FACTOR,
            ),
            "base": base_growth,
            "optimistic": base_growth * OPTIMISTIC_GROWTH_FACTOR,
        }

        months = self.months
        out = {
            "inputs": inputs,
            "months": months,
            "scenarios": {},
            "warnings": warnings,
        }

        for name, g in scenarios.items():
            proj = self._build_projection(
                start_rev=inputs["revenue_monthly"],
                growth=g,
                months=months,
                gross_margin=inputs["gross_margin"],
                fixed_monthly=inputs["fixed_monthly_costs"],
            )

            cum_net = cumulative(proj["net_cashflow"])
            breakeven = self._breakeven_month(cum_net)
            year1 = monthly_to_annual(proj["net_cashflow"][:12])
            year2 = monthly_to_annual(proj["net_cashflow"][12:24]) if months >= 24 else None

            cac_ltv_res = cac_ltv(
                inputs["cac"],
                inputs["arpu_monthly"],
                inputs["gross_margin"],
                inputs["churn_monthly"],
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
                "cac_ltv": cac_ltv_res,
            }

        out["summary"] = {
            "revenue_monthly_start": inputs["revenue_monthly"],
            "arpu_monthly": inputs["arpu_monthly"],
            "cac": inputs["cac"],
            "gross_margin": inputs["gross_margin"],
            "input_sources": inputs["_sources"],
        }

        # Keep the long-range revenue view separate from the 24-month cash-flow
        # scenarios: it is useful for valuation context but is more speculative.
        five_year = multi_year_financial_table(
            start_monthly_revenue=inputs["revenue_monthly"],
            monthly_growth=inputs["growth_monthly"],
            months=LONG_RANGE_MONTHS,
        )

        out["five_year_projection"] = {
            "annual_revenue": five_year["annual"],
            "monthly_revenue": five_year["monthly"],
        }

        if overrides.get("explain", False):
            try:
                prompt = (
                    "Explain these financial projections succinctly.\n\n"
                    f"INPUTS:\n{json.dumps(inputs, indent=2)}\n\n"
                    f"SCENARIOS:\n{json.dumps(list(out['scenarios'].keys()), indent=2)}"
                )
                out["llm_explanation"] = call_llm(prompt)
            except Exception as e:
                out["llm_explanation_error"] = str(e)

        return out
