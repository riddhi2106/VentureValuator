import pytest

from agents.financial_agent import FinancialAgent


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

