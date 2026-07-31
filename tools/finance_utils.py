# tools/finance_utils.py

"""
Utility functions used by FinancialAgent.
These are pure math helpers:
- monthly_growth_series()
- cumulative()
- cac_ltv()
- monthly_to_annual()
"""

from typing import Any, Dict, List


def monthly_growth_series(start: float, growth: float, months: int) -> List[float]:
    """Project monthly revenue using compound growth.

    ``start`` represents month one, so the first value is unchanged and the
    formula for month ``i`` is ``start * (1 + growth) ** i``. Growth may be
    negative, but values below ``-1`` are not meaningful for this model.
    """

    if months < 0:
        raise ValueError("months must be non-negative")
    if growth < -1:
        raise ValueError("growth cannot be less than -100%")
    return [start * ((1 + growth) ** month) for month in range(months)]


def cumulative(values: List[float]) -> List[float]:
    """Return the running total used for cumulative net cash flow."""

    out = []
    total = 0.0
    for v in values:
        total += v
        out.append(total)
    return out


def cac_ltv(
    cac: float,
    arpu_monthly: float,
    gross_margin: float,
    churn_monthly: float,
) -> Dict[str, Any]:
    """Estimate customer lifetime value and the LTV-to-CAC ratio.

    This intentionally uses the transparent steady-state approximation
    ``LTV = monthly ARPU * gross margin / monthly churn``. A 0.1% churn floor
    prevents infinite lifetime values when a deck reports zero or omits churn.
    The result should be treated as a directional diligence metric rather than
    a cohort-based valuation.
    """

    if churn_monthly <= 0:
        churn_monthly = 0.001

    ltv = (arpu_monthly * gross_margin) / churn_monthly
    ratio = ltv / cac if cac else None

    return {
        "ltv": ltv,
        "cac": cac,
        "ltv_cac_ratio": ratio,
    }


def monthly_to_annual(month_values: List[float]) -> float:
    """Aggregate up to twelve monthly values into an annual total."""

    return sum(month_values)


def yearly_growth_projection(
    start_year_revenue: float,
    annual_growth: float,
    years: int = 5,
) -> List[float]:
    """Project annual revenue using a constant year-over-year growth rate."""

    if years < 0:
        raise ValueError("years must be non-negative")
    projection = []
    current = start_year_revenue

    for _ in range(years):
        projection.append(current)
        current *= (1 + annual_growth)

    return projection


def multi_year_financial_table(
    start_monthly_revenue: float,
    monthly_growth: float,
    months: int = 60,
) -> Dict[str, List[float]]:
    """Return monthly projections and calendar-year revenue aggregates.

    Partial final years are included, which keeps the annual output consistent
    when callers request a horizon other than the default 60 months.
    """

    monthly_values = monthly_growth_series(
        start_monthly_revenue,
        monthly_growth,
        months,
    )
    annual_values = [
        sum(monthly_values[start : start + 12])
        for start in range(0, months, 12)
    ]

    return {
        "monthly": monthly_values,
        "annual": annual_values,
    }
