from agents.financial_agent import FinancialAgent
from agents.memo_agent import MemoAgent


def _score(extracted, market=None, skeptic=None):
    financial = FinancialAgent().run(extracted)
    return MemoAgent(use_llm=False).evaluate(
        extracted,
        market or {},
        financial,
        skeptic or {},
    )


def test_evidence_driven_rubric_separates_weak_and_strong_startups():
    weak = {
        "problem": "A vague problem",
        "solution": "An app",
        "notable_metrics": {},
    }
    strong = {
        "problem": [
            "Enterprise finance teams lose 30 hours each month reconciling invoices.",
            "Errors delay the monthly close and create material compliance exposure.",
        ],
        "solution": [
            "Automated reconciliation with native ERP integrations.",
            "Exception review reduces manual work and creates an audit trail.",
        ],
        "target_customer": "Enterprise financial controllers",
        "business_model": "Annual SaaS contracts",
        "pricing": "$24,000 annual contract value",
        "gtm_strategy": "Enterprise sales plus ERP marketplace and channel partnerships",
        "team": "Former payments engineering lead and enterprise software sales director",
        "competition": ["BlackLine", "Trintech"],
        "notable_metrics": {
            "revenue_last_month": "$180,000",
            "mom_growth": "18%",
            "mau": "15,000",
            "gross_margin": "72%",
            "cac": "$4,200",
            "churn": "1.5%",
            "nps": "68",
        },
    }
    market = {
        "tam": "$12B",
        "sam": "$2.5B",
        "market_growth_rate": "21%",
        "key_trends": ["AI automation", "ERP modernization"],
        "competitive_landscape": {
            "direct_competitors": ["BlackLine"],
            "competitive_advantages": ["Faster implementation", "Native integrations"],
        },
        "sources": [
            {"url": "https://example.com/market"},
            {"url": "https://example.com/growth"},
        ],
    }

    weak_result = _score(weak)
    strong_result = _score(strong, market)

    assert weak_result["rubric_version"] == 2
    assert strong_result["overall"]["score"] >= weak_result["overall"]["score"] + 4
    assert strong_result["overall"]["confidence"] > weak_result["overall"]["confidence"]
    assert "extracted.notable_metrics.revenue_last_month" in strong_result["dimensions"][
        "traction_metrics"
    ]["evidence"]
    assert "https://example.com/market" in strong_result["dimensions"]["market_timing"][
        "evidence"
    ]


def test_skeptic_penalties_target_relevant_dimensions():
    extracted = {
        "problem": "Finance teams need automated reconciliation",
        "solution": "Automated reconciliation software",
        "target_customer": "Finance teams",
        "business_model": "SaaS",
        "gtm_strategy": "Direct sales",
        "notable_metrics": {"revenue_last_month": "$50,000", "mau": "1,500"},
    }
    baseline = _score(extracted)
    penalized = _score(
        extracted,
        skeptic={
            "red_flags": ["CAC and LTV are not evidenced"],
            "missing_data": ["Churn and gross margin are missing"],
        },
    )

    base_dimensions = baseline["dimensions"]
    penalized_dimensions = penalized["dimensions"]
    assert (
        penalized_dimensions["unit_economics"]["score"]
        < base_dimensions["unit_economics"]["score"]
    )
    assert penalized["overall"]["score"] < baseline["overall"]["score"]
