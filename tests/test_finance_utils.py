import pytest

from tools.finance_utils import (
    cac_ltv,
    cumulative,
    monthly_growth_series,
    monthly_to_annual,
    multi_year_financial_table,
    yearly_growth_projection,
)


def test_monthly_growth_series_handles_growth_and_contraction():
    assert monthly_growth_series(100, 0.10, 3) == pytest.approx([100, 110, 121])
    assert monthly_growth_series(100, -0.10, 3) == pytest.approx([100, 90, 81])


def test_growth_projections_reject_invalid_horizons_and_rates():
    with pytest.raises(ValueError, match="months"):
        monthly_growth_series(100, 0.10, -1)
    with pytest.raises(ValueError, match="100%"):
        monthly_growth_series(100, -1.01, 12)
    with pytest.raises(ValueError, match="years"):
        yearly_growth_projection(1_000, 0.2, years=-1)


def test_cumulative_and_annual_total():
    values = [100, -25, 50]
    assert cumulative(values) == pytest.approx([100, 75, 125])
    assert monthly_to_annual(values) == pytest.approx(125)


def test_cac_ltv_calculates_ratio_and_handles_zero_churn():
    result = cac_ltv(cac=100, arpu_monthly=50, gross_margin=0.8, churn_monthly=0.05)
    assert result["ltv"] == pytest.approx(800)
    assert result["ltv_cac_ratio"] == pytest.approx(8)

    zero_churn = cac_ltv(cac=0, arpu_monthly=50, gross_margin=0.8, churn_monthly=0)
    assert zero_churn["ltv"] == pytest.approx(40_000)
    assert zero_churn["ltv_cac_ratio"] is None


def test_long_range_projections_have_expected_shape():
    yearly = yearly_growth_projection(1_000, 0.20, years=3)
    assert yearly == pytest.approx([1_000, 1_200, 1_440])

    table = multi_year_financial_table(1_000, 0.0, months=60)
    assert len(table["monthly"]) == 60
    assert table["annual"] == pytest.approx([12_000] * 5)


def test_multi_year_projection_includes_partial_final_year():
    table = multi_year_financial_table(1_000, 0.0, months=14)
    assert table["annual"] == pytest.approx([12_000, 2_000])
