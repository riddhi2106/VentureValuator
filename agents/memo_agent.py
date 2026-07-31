"""
MemoAgent with weighted 6-dimension scoring rubric and LLM-generated insights.
"""

import json
import re
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


def _numeric(value) -> float | None:
    if value in (None, "", []):
        return None
    text = str(value).lower().replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = float(match.group())
    if "billion" in text or re.search(r"\d\s*b\b", text):
        number *= 1_000_000_000
    elif "million" in text or re.search(r"\d\s*m\b", text):
        number *= 1_000_000
    elif "lakh" in text:
        number *= 100_000
    elif "crore" in text:
        number *= 10_000_000
    return number


def _content_depth(value) -> int:
    if not _has_content(value):
        return 0
    if isinstance(value, list):
        return sum(len(str(item).split()) for item in value)
    return len(str(value).split())


def _score_problem_clarity(extracted: dict) -> tuple[float, str]:
    score = 1.5
    notes = []
    problem = extracted.get("problem")
    solution = extracted.get("solution")
    if _has_content(problem):
        depth = _content_depth(problem)
        score += 2.0 if depth >= 18 else 1.0
        notes.append("Problem is specific" if depth >= 18 else "Problem is stated but thin")
    else:
        notes.append("Problem evidence missing")
    if _has_content(solution):
        depth = _content_depth(solution)
        score += 2.0 if depth >= 18 else 1.0
        notes.append("Solution is well described" if depth >= 18 else "Solution detail is limited")
    if _has_content(extracted.get("target_customer")):
        score += 1.5
        notes.append("Target customer identified")
    if _has_content(extracted.get("pricing")):
        score += 1.0
        notes.append("Customer value is tied to pricing")
    return min(10.0, score), "; ".join(notes)


def _score_market_timing(market: dict) -> tuple[float, str]:
    score = 1.5
    notes = []
    sources = [s for s in (market.get("sources") or []) if s.get("url")]
    tam = _numeric(market.get("tam"))
    sam = _numeric(market.get("sam"))
    growth = _numeric(market.get("market_growth_rate"))
    if tam:
        score += 1.5
        notes.append("TAM quantified")
    if sam:
        score += 1.0
        notes.append("SAM quantified")
    if growth is not None:
        score += 2.0 if growth >= 15 else (1.25 if growth >= 5 else 0.5)
        notes.append(f"Market growth reported at ~{growth:g}%")
    if market.get("key_trends") and len(market.get("key_trends", [])) >= 2:
        score += 1.0
        notes.append("Market trends identified")
    if len(sources) >= 2:
        score += 2.0
        notes.append("Claims supported by multiple sources")
    elif sources:
        score += 0.75
        notes.append("Limited source support")
    else:
        notes.append("Market claims are not source-backed")
    return min(10.0, score), "; ".join(notes)


def _score_traction(extracted: dict) -> tuple[float, str]:
    score = 1.0
    notes = []
    metrics = _get_metrics(extracted)
    revenue = metrics.get("revenue_last_month") or metrics.get("Last month revenue")
    mau = metrics.get("mau") or metrics.get("Monthly active users")
    growth = metrics.get("mom_growth") or metrics.get("Month-over-month growth")

    revenue_n = _numeric(revenue)
    mau_n = _numeric(mau)
    growth_n = _numeric(growth)
    if revenue_n is not None:
        score += 2.5 if revenue_n >= 100_000 else (1.75 if revenue_n >= 10_000 else 1.0)
        notes.append(f"Monthly revenue evidence: {revenue}")
    if mau_n is not None:
        score += 2.0 if mau_n >= 10_000 else (1.25 if mau_n >= 1_000 else 0.75)
        notes.append(f"Usage evidence: {mau}")
    if growth_n is not None:
        score += 2.0 if growth_n >= 15 else (1.25 if growth_n > 0 else 0.25)
        notes.append(f"Growth evidence: {growth}")
    if len([k for k, v in metrics.items() if v]) >= 4:
        score += 1.5
        notes.append("Rich metrics package")
    if not notes:
        notes.append("No quantified traction in the deck")
    return min(10.0, score), "; ".join(notes)


def _score_unit_economics(financial: dict) -> tuple[float, str]:
    score = 1.5
    notes = []
    summary = financial.get("summary", {})
    sources = summary.get("input_sources") or {}
    if sources.get("revenue_monthly") == "deck":
        score += 2.0
        notes.append("Revenue baseline comes from deck")
    else:
        notes.append("Revenue baseline is assumed")
    if sources.get("gross_margin") == "deck" and summary.get("gross_margin") is not None:
        gm = summary["gross_margin"]
        score += 2.0 if gm >= 0.6 else (1.25 if gm >= 0.4 else 0.5)
        notes.append(f"Deck-sourced gross margin ~{gm * 100:.0f}%")
    else:
        notes.append("Gross margin is modeled, not evidenced")
    if sources.get("cac") == "deck":
        score += 1.5
        notes.append("CAC estimated")
    base = financial.get("scenarios", {}).get("base", {})
    cac_ltv = base.get("cac_ltv", {})
    ratio = cac_ltv.get("ltv_cac_ratio")
    if ratio and sources.get("cac") != "assumption" and sources.get("arpu_monthly") != "assumption":
        score += 2.0 if ratio >= 3 else (1.0 if ratio >= 1 else 0.25)
        notes.append(f"LTV/CAC modeled at {ratio:.1f}x from available evidence")
    return min(10.0, score), "; ".join(notes) if notes else "Unit economics not fully evidenced"


def _score_competitive_moat(extracted: dict, market: dict) -> tuple[float, str]:
    score = 1.5
    notes = []
    landscape = market.get("competitive_landscape") or {}
    advantages = landscape.get("competitive_advantages") or []
    competitors = landscape.get("direct_competitors") or []
    deck_competition = extracted.get("competition") or []

    if advantages:
        score += min(2.0, len(advantages) * 0.75)
        notes.append("Potential advantages identified")
    if competitors or deck_competition:
        score += 1.5 if deck_competition else 0.75
        notes.append("Competitive landscape mapped")
    if len(advantages) >= 2 and _content_depth(extracted.get("solution")) >= 18:
        score += 1.25
        notes.append("Differentiation has supporting product detail")
    risks = landscape.get("competitive_risks") or []
    if len(risks) >= 2:
        score -= 0.5
        notes.append("Material competitive risks remain")
    return min(10.0, score), "; ".join(notes) if notes else "Weak competitive positioning evidence"


def _score_gtm_team(extracted: dict) -> tuple[float, str]:
    score = 1.0
    notes = []
    if _has_content(extracted.get("gtm_strategy")):
        score += 2.5 if _content_depth(extracted.get("gtm_strategy")) >= 15 else 1.5
        notes.append("GTM strategy outlined")
    if _has_content(extracted.get("business_model")):
        score += 1.5
        notes.append("Business model clear")
    if _has_content(extracted.get("pricing")):
        score += 1.0
        notes.append("Pricing defined")
    if _has_content(extracted.get("team")):
        score += 2.5 if _content_depth(extracted.get("team")) >= 15 else 1.25
        notes.append("Team experience provided")
    else:
        notes.append("Team evidence missing")
    return min(10.0, score), "; ".join(notes) if notes else "GTM/team details sparse"


def _apply_skeptic_penalty(dimensions: dict, skeptic: dict) -> dict:
    if not skeptic or skeptic.get("error"):
        return dimensions

    red_flags = skeptic.get("red_flags") or []
    missing = skeptic.get("missing_data") or []
    concerns = " ".join(str(item).lower() for item in red_flags + missing)
    penalties = {key: min(0.6, len(red_flags) * 0.08 + len(missing) * 0.05) for key in dimensions}
    keyword_map = {
        "traction_metrics": ("revenue", "traction", "retention", "churn", "growth", "customer"),
        "unit_economics": ("cac", "ltv", "margin", "burn", "runway", "economics"),
        "market_timing": ("tam", "sam", "market", "source"),
        "competitive_moat": ("compet", "moat", "defensib", "differentiat"),
        "gtm_team": ("team", "founder", "gtm", "sales", "distribution"),
        "problem_clarity": ("problem", "customer", "solution", "use case"),
    }
    for key, keywords in keyword_map.items():
        penalties[key] += min(1.2, sum(0.3 for word in keywords if word in concerns))

    for key, penalty in penalties.items():
        dimensions[key]["score"] = round(max(0, dimensions[key]["score"] - penalty), 2)
    dimensions["_skeptic_penalty"] = round(
        sum(penalties.values()) / max(1, len(penalties)),
        2,
    )
    return dimensions


def _verdict_from_score(score: float) -> str:
    if score >= 7.5:
        return "Invest"
    if score >= 6.0:
        return "Pass"
    if score >= 5.0:
        return "Neutral"
    return "Avoid"


def _evidence_confidence(extracted, market, financial, skeptic) -> float:
    metrics = _get_metrics(extracted)
    sources = [s for s in (market.get("sources") or []) if s.get("url")]
    input_sources = financial.get("summary", {}).get("input_sources") or {}
    deck_financials = sum(1 for source in input_sources.values() if source == "deck")
    core_fields = ("problem", "solution", "target_customer", "business_model", "gtm_strategy", "team")
    filled_fields = sum(1 for field in core_fields if _has_content(extracted.get(field)))
    missing = len((skeptic or {}).get("missing_data") or [])

    confidence = (
        0.25
        + min(0.18, filled_fields * 0.03)
        + min(0.18, len([v for v in metrics.values() if v]) * 0.03)
        + min(0.18, len(sources) * 0.06)
        + min(0.15, deck_financials * 0.05)
        - min(0.18, missing * 0.03)
    )
    return round(max(0.30, min(0.92, confidence)), 2)


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
        verdict = _verdict_from_score(overall_score)
        confidence = _evidence_confidence(
            extracted,
            market,
            financial,
            skeptic or {},
        )

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
            "rubric_version": 2,
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
