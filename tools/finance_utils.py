# tools/finance_utils.py

"""
Utility functions used by FinancialAgent.
These are pure math helpers:
- monthly_growth_series()
- cumulative()
- cac_ltv()
- monthly_to_annual()
"""

from typing import List, Dict, Any
import math

def monthly_growth_series(start: float, growth: float, months: int) -> List[float]:
    """
    Return a monthly revenue series:
      revenue[i] = start * (1 + growth)^i
    growth may be negative (contraction) or positive.
    """
    series = []
    for i in range(months):
        series.append(start * ((1 + growth) ** i))
    return series


def cumulative(values: List[float]) -> List[float]:
    """
    Return cumulative sum of a list.
    """
    out = []
    total = 0.0
    for v in values:
        total += v
        out.append(total)
    return out


def cac_ltv(cac: float, arpu_monthly: float, gross_margin: float, churn_monthly: float) -> Dict[str, Any]:
    """
    Compute:
    - LTV = (ARPU_monthly * gross_margin) / churn_monthly     [simple formula]
    - CAC:LTV ratio
    """
    if churn_monthly <= 0:
        churn_monthly = 0.001  # avoid divide-by-zero

    ltv = (arpu_monthly * gross_margin) / churn_monthly
    ratio = ltv / cac if cac else None

    return {
        "ltv": ltv,
        "cac": cac,
        "ltv_cac_ratio": ratio
    }


def monthly_to_annual(month_values: List[float]) -> float:
    """
    Convert a monthly list into an annual total.
    """
    return sum(month_values)


def yearly_growth_projection(start_year_revenue: float, annual_growth: float, years: int = 5):
    """
    Creates a 5-year YoY revenue projection.
    """
    projection = []
    current = start_year_revenue

    for _ in range(years):
        projection.append(current)
        current *= (1 + annual_growth)

    return projection


def multi_year_financial_table(start_monthly_revenue: float,
                               monthly_growth: float,
                               months: int = 60):
    """
    Builds a 60-month (5-year) monthly revenue model.
    We reuse monthly_growth_series to compute monthly numbers.
    Then aggregate each 12-month chunk into annual totals.
    """
    monthly_values = monthly_growth_series(start_monthly_revenue,
                                           monthly_growth,
                                           months)

    annual_values = []
    for yr in range(5):
        chunk = monthly_values[yr * 12:(yr + 1) * 12]
        annual_values.append(sum(chunk))

    return {
        "monthly": monthly_values,
        "annual": annual_values
    }
