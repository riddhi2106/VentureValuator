"""
MemoAgent with weighted 6-dimension scoring rubric and LLM-generated insights.
"""

from typing import Dict, Any
import json
import textwrap
from tools.llm_client import call_llm

MAX_BULLETS = 6

RUBRIC_WEIGHTS = {
    "problem_clarity": 0.15,
    "market_timing": 0.20,
    "traction_metrics": 0.20,
    "unit_economics": 0.20,
    "competitive_moat": 0.15,
    "gtm_team": 0.10,
}


def _extract_bullets(data, limit=MAX_BULLETS):
    if not data:
        return []
    if isinstance(data, list):
        return data[:limit]
    txt = str(data)
    parts = [p.strip() for p in txt.split(".") if p.strip()]
    return parts[:limit]


def _compact(s, n=300):
    if not s:
        return ""
    if isinstance(s, list):
        s = ". ".join(str(x) for x in s if x)
    else:
        s = str(s)
    s = " ".join(s.split())
    if len(s) <= n:
        return s
    return s[:n] + "..."


def _has_content(val) -> bool:
    if not val:
        return False
    if isinstance(val, (list, dict)):
        return len(val) > 0
    return bool(str(val).strip())


def _get_metrics(extracted: dict) -> dict:
    return extracted.get("notable_metrics") or {}


def _score_problem_clarity(extracted: dict) -> tuple[float, str]:
    score = 4.0
    notes = []
    problem = extracted.get("problem")
    solution = extracted.get("solution")
    if _has_content(problem):
        score += 2.0 if isinstance(problem, list) and len(problem) >= 2 else 1.0
        notes.append("Problem articulated")
    else:
        notes.append("Problem unclear or missing")
    if _has_content(solution):
        score += 2.0
        notes.append("Solution defined")
    if _has_content(extracted.get("target_customer")):
        score += 1.0
        notes.append("Target customer identified")
    return min(10.0, score), "; ".join(notes)


def _score_market_timing(market: dict) -> tuple[float, str]:
    score = 4.0
    notes = []
    if market.get("tam"):
        score += 2.0
        notes.append("TAM provided")
    if market.get("market_growth_rate"):
        score += 1.5
        notes.append("Growth rate cited")
    if market.get("key_trends") and len(market.get("key_trends", [])) >= 2:
        score += 1.5
        notes.append("Market trends identified")
    if market.get("sources") and len(market.get("sources", [])) >= 2:
        score += 1.0
        notes.append("Web-cited research")
    return min(10.0, score), "; ".join(notes)


def _score_traction(extracted: dict) -> tuple[float, str]:
    score = 3.0
    notes = []
    metrics = _get_metrics(extracted)
    revenue = metrics.get("revenue_last_month") or metrics.get("Last month revenue")
    mau = metrics.get("mau") or metrics.get("Monthly active users")
    growth = metrics.get("mom_growth") or metrics.get("Month-over-month growth")

    if revenue:
        score += 2.5
        notes.append("Revenue data present")
    if mau:
        score += 2.0
        notes.append("User/traction metrics present")
    if growth:
        score += 1.5
        notes.append("Growth rate provided")
    if len([k for k, v in metrics.items() if v]) >= 4:
        score += 1.0
        notes.append("Rich metrics package")
    if not notes:
        notes.append("Limited traction data in deck")
    return min(10.0, score), "; ".join(notes)


def _score_unit_economics(financial: dict) -> tuple[float, str]:
    score = 4.0
    notes = []
    summary = financial.get("summary", {})
    if summary.get("revenue_monthly_start"):
        score += 2.0
        notes.append("Revenue baseline modeled")
    if summary.get("gross_margin") is not None:
        gm = summary["gross_margin"]
        score += 1.5 if gm >= 0.4 else 0.5
        notes.append(f"Gross margin ~{gm * 100:.0f}%")
    if summary.get("cac"):
        score += 1.0
        notes.append("CAC estimated")
    base = financial.get("scenarios", {}).get("base", {})
    cac_ltv = base.get("cac_ltv", {})
    if cac_ltv.get("ltv_cac_ratio") and cac_ltv["ltv_cac_ratio"] > 2:
        score += 1.5
        notes.append("LTV/CAC ratio healthy")
    return min(10.0, score), "; ".join(notes) if notes else "Unit economics not fully evidenced"


def _score_competitive_moat(extracted: dict, market: dict) -> tuple[float, str]:
    score = 4.0
    notes = []
    landscape = market.get("competitive_landscape") or {}
    advantages = landscape.get("competitive_advantages") or []
    competitors = landscape.get("direct_competitors") or []
    deck_competition = extracted.get("competition") or []

    if advantages:
        score += 2.0
        notes.append("Competitive advantages stated")
    if competitors or deck_competition:
        score += 1.5
        notes.append("Competitive landscape mapped")
    if _has_content(extracted.get("solution")) and len(advantages) >= 2:
        score += 1.5
        notes.append("Differentiation appears credible")
    return min(10.0, score), "; ".join(notes) if notes else "Weak competitive positioning evidence"


def _score_gtm_team(extracted: dict) -> tuple[float, str]:
    score = 4.0
    notes = []
    if _has_content(extracted.get("gtm_strategy")):
        score += 3.0
        notes.append("GTM strategy outlined")
    if _has_content(extracted.get("business_model")):
        score += 2.0
        notes.append("Business model clear")
    if _has_content(extracted.get("pricing")):
        score += 1.0
        notes.append("Pricing defined")
    return min(10.0, score), "; ".join(notes) if notes else "GTM/team details sparse"


def _apply_skeptic_penalty(dimensions: dict, skeptic: dict) -> dict:
    if not skeptic or skeptic.get("error"):
        return dimensions

    red_flags = skeptic.get("red_flags") or []
    missing = skeptic.get("missing_data") or []
    penalty = min(1.5, len(red_flags) * 0.3 + len(missing) * 0.15)

    if penalty > 0:
        for key in dimensions:
            dimensions[key]["score"] = max(0, dimensions[key]["score"] - penalty * 0.5)
        dimensions["_skeptic_penalty"] = round(penalty, 2)
    return dimensions


def _verdict_from_score(score: float) -> tuple[str, float]:
    if score >= 7.5:
        return "Invest", 0.85
    if score >= 6.0:
        return "Pass", 0.70
    if score >= 5.0:
        return "Neutral", 0.55
    return "Avoid", 0.40


def _llm_insights(extracted, market, financial, skeptic, dimensions) -> dict:
    prompt = f"""
You are a VC analyst writing the evaluation section of an investment memo.

Based on the data below, return ONLY valid JSON:
{{
  "strengths": ["specific strength citing deck/market/financial data"],
  "risks": ["specific risk citing deck/market/financial data"]
}}

Provide 3-5 strengths and 3-5 risks. Be specific — reference actual numbers, competitors, or gaps.
Do NOT use generic phrases like "good fundamentals" or "limited data".

EXTRACTED: {json.dumps(extracted, indent=2)[:3000]}
MARKET: {json.dumps(market, indent=2)[:2000]}
FINANCIAL SUMMARY: {json.dumps(financial.get("summary", {}), indent=2)}
SKEPTIC REVIEW: {json.dumps(skeptic, indent=2)[:2000]}
DIMENSION SCORES: {json.dumps({k: v["score"] for k, v in dimensions.items() if not k.startswith("_")}, indent=2)}
"""
    try:
        resp = call_llm(prompt)
        clean = resp.replace("```json", "").replace("```", "").strip()
        start, end = clean.find("{"), clean.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(clean[start:end])
    except Exception:
        pass
    return {}


def _memo_text(title, extraction, market, financial_bullets, evaluation, skeptic=None):
    lines = [title, "=" * len(title)]

    if extraction.get("one_liner"):
        lines.extend(["\nOne-liner:", extraction["one_liner"]])

    lines.append("\nCompany Overview:")
    for b in extraction.get("problem", []):
        lines.append("  • Problem: " + b)
    for b in extraction.get("solution", []):
        lines.append("  • Solution: " + b)
    if extraction.get("business_model"):
        lines.append(f"  • Business model: {extraction['business_model']}")

    lines.append("\nMarket Summary:")
    if market.get("market_category"):
        lines.append(f"  • Category: {market['market_category']}")
    if market.get("tam"):
        lines.append(f"  • TAM: {market['tam']}")
    for t in market.get("key_trends", []):
        lines.append(f"  • Trend: {t}")

    lines.append("\nFinancial Highlights:")
    for f in financial_bullets:
        lines.append(f"  • {f}")

    o = evaluation["overall"]
    lines.extend([
        "\nEvaluation Summary:",
        f"  • Score: {o['score']:.2f}/10",
        f"  • Verdict: {o['verdict']} (confidence {o['confidence']:.0%})",
    ])

    dims = evaluation.get("dimensions", {})
    if dims:
        lines.append("\nDimension Scores:")
        for name, data in dims.items():
            if name.startswith("_"):
                continue
            label = name.replace("_", " ").title()
            lines.append(f"  • {label}: {data['score']:.1f}/10 — {data.get('rationale', '')}")

    lines.append("\nStrengths:")
    for s in evaluation.get("strengths", []):
        lines.append(f"  • {s}")
    lines.append("\nRisks:")
    for r in evaluation.get("risks", []):
        lines.append(f"  • {r}")

    if skeptic and not skeptic.get("error"):
        lines.append("\nSkeptical VC Review:")
        if skeptic.get("skeptic_summary"):
            lines.append(f"  {skeptic['skeptic_summary']}")
        for q in (skeptic.get("partner_questions") or [])[:5]:
            lines.append(f"  ? {q}")

    return "\n".join([textwrap.fill(p, 90) if len(p) > 90 else p for p in lines])


class MemoAgent:
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm

    def evaluate(self, extracted, market, financial, skeptic=None) -> dict:
        scorers = {
            "problem_clarity": _score_problem_clarity(extracted),
            "market_timing": _score_market_timing(market),
            "traction_metrics": _score_traction(extracted),
            "unit_economics": _score_unit_economics(financial),
            "competitive_moat": _score_competitive_moat(extracted, market),
            "gtm_team": _score_gtm_team(extracted),
        }

        dimensions = {
            key: {"score": score, "weight": RUBRIC_WEIGHTS[key], "rationale": rationale}
            for key, (score, rationale) in scorers.items()
        }
        dimensions = _apply_skeptic_penalty(dimensions, skeptic or {})

        overall_score = sum(
            d["score"] * d["weight"]
            for k, d in dimensions.items()
            if not k.startswith("_")
        )
        verdict, confidence = _verdict_from_score(overall_score)

        strengths, risks = [], []
        if self.use_llm:
            insights = _llm_insights(extracted, market, financial, skeptic or {}, dimensions)
            strengths = insights.get("strengths") or []
            risks = insights.get("risks") or []

        if not strengths:
            strengths = [d["rationale"] for k, d in dimensions.items() if not k.startswith("_") and d["score"] >= 7][:4]
        if not risks:
            if skeptic:
                risks = (skeptic.get("red_flags") or [])[:4]
            if not risks:
                risks = [d["rationale"] for k, d in dimensions.items() if not k.startswith("_") and d["score"] < 6][:4]

        return {
            "overall": {
                "score": round(overall_score, 2),
                "verdict": verdict,
                "confidence": confidence,
            },
            "dimensions": dimensions,
            "strengths": strengths,
            "risks": risks,
        }

    def run(self, extracted, market, financial, skeptic=None, explain=False):
        extraction = {
            "name": extracted.get("name") or extracted.get("company_name") or "Startup",
            "one_liner": _compact(extracted.get("solution") or extracted.get("problem") or "", 200),
            "problem": _extract_bullets(extracted.get("problem", "")),
            "solution": _extract_bullets(extracted.get("solution", "")),
            "business_model": _compact(extracted.get("business_model", ""), 300),
        }

        market_c = {
            "market_category": market.get("market_category"),
            "tam": market.get("tam"),
            "growth_rate": market.get("market_growth_rate"),
            "key_trends": _extract_bullets(market.get("key_trends", [])),
        }

        financial_bullets = []
        summary = financial.get("summary", {})
        if summary.get("revenue_monthly_start"):
            financial_bullets.append(f"Monthly revenue: ${summary['revenue_monthly_start']:,.0f}")
        if summary.get("gross_margin") is not None:
            financial_bullets.append(f"Gross margin: {summary['gross_margin'] * 100:.1f}%")
        if summary.get("cac"):
            financial_bullets.append(f"CAC: ${summary['cac']:,.0f}")

        evaluation = self.evaluate(extracted, market, financial, skeptic)

        memo_json = {
            "title": f"Investor Memo — {extraction['name']}",
            "sections": {
                "overview": extraction,
                "market": market_c,
                "financial": financial_bullets,
            },
            "evaluation": evaluation,
        }

        memo_text = _memo_text(
            memo_json["title"], extraction, market_c, financial_bullets, evaluation, skeptic
        )

        return {
            "memo_json": memo_json,
            "memo_text": memo_text,
            "evaluation": evaluation,
        }
