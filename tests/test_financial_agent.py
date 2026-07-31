import pytest

from agents.financial_agent import FinancialAgent, _parse_money_to_float


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("$1.5m", 1_500_000),
        ("₹2 lakh", 200_000),
        ("3b", 3_000_000_000),
        ("not disclosed", None),
    ],
)
def test_money_parser_supports_deck_formats(raw, expected):
    assert _parse_money_to_float(raw) == expected


def test_financial_agent_rejects_non_positive_horizon():
    with pytest.raises(ValueError, match="positive"):
        FinancialAgent(months=0)


def test_financial_agent_marks_missing_inputs_as_assumptions():
    result = FinancialAgent(months=24).run({"notable_metrics": {}})
    summary = result["summary"]

    assert summary["revenue_monthly_start"] == 100_000
    assert summary["input_sources"]["revenue_monthly"] == "assumption"
    assert summary["input_sources"]["gross_margin"] == "assumption"
    assert summary["input_sources"]["cac"] == "assumption"
    assert len(result["scenarios"]["base"]["revenue_series"]) == 24


def test_financial_agent_uses_and_labels_deck_metrics():
    extracted = {
        "notable_metrics": {
            "revenue_last_month": "$200,000",
            "mom_growth": "12%",
            "mau": "4,000",
            "gross_margin": "70%",
            "cac": "$300",
            "churn": "2%",
            "burn_monthly": "$80,000",
        }
    }
    result = FinancialAgent().run(extracted)
    summary = result["summary"]
    sources = summary["input_sources"]

    assert summary["revenue_monthly_start"] == 200_000
    assert summary["gross_margin"] == pytest.approx(0.70)
    assert summary["cac"] == 300
    assert sources["revenue_monthly"] == "deck"
    assert sources["growth_monthly"] == "deck"
    assert sources["gross_margin"] == "deck"
    assert sources["cac"] == "deck"
    assert sources["churn_monthly"] == "deck"
    assert sources["fixed_monthly_costs"] == "deck"


def test_financial_scenarios_are_ordered_by_growth():
    result = FinancialAgent().run(
        {"notable_metrics": {"revenue_last_month": "10000", "mom_growth": "10%"}}
    )
    month_24 = {
        name: scenario["revenue_series"][-1]
        for name, scenario in result["scenarios"].items()
    }
    assert month_24["conservative"] < month_24["base"] < month_24["optimistic"]


def test_overrides_drive_sensitivity_without_losing_input_provenance():
    result = FinancialAgent(months=2).run(
        {"notable_metrics": {"revenue_last_month": "$10,000"}},
        overrides={"growth_monthly": 0.0, "fixed_monthly_costs": 1_000},
    )

    assert result["scenarios"]["base"]["revenue_series"] == [10_000, 10_000]
    assert result["scenarios"]["base"]["net_cashflow"] == [1_500, 1_500]
    assert result["summary"]["input_sources"]["revenue_monthly"] == "deck"


def test_financial_agent_sanitizes_impossible_inputs_and_growth():
    result = FinancialAgent(months=2).run(
        {
            "notable_metrics": {
                "revenue_last_month": "$10,000",
                "mom_growth": "350%",
                "gross_margin": "140%",
                "churn": "0%",
            }
        }
    )

    assert result["inputs"]["growth_monthly"] == 1.0
    assert result["inputs"]["gross_margin"] == 0.25
    assert result["inputs"]["churn_monthly"] == 0.05
    assert result["summary"]["input_sources"]["gross_margin"] == "assumption"
    assert len(result["warnings"]) == 3
