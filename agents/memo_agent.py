"""
Simplified MemoAgent:
- NO saving files
- NO PDF generation
- Only returns memo_text + memo_json + evaluation + optional llm_explanation

Streamlit will handle downloads directly.
"""

from typing import Dict, Any
import json
import textwrap
from tools.llm_client import call_gemini

MAX_BULLETS = 6

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
    s = " ".join(s.split())
    if len(s) <= n:
        return s
    return s[:n] + "..."

def _memo_text(title, extraction, market, financial_bullets, evaluation):
    lines = []
    lines.append(title)
    lines.append("=" * len(title))

    if extraction.get("one_liner"):
        lines.append("\nOne-liner:")
        lines.append(extraction["one_liner"])

    lines.append("\nCompany Overview:")
    if extraction["problem"]:
        lines.append("- Problem:")
        for b in extraction["problem"]:
            lines.append("  • " + b)

    if extraction["solution"]:
        lines.append("- Solution:")
        for b in extraction["solution"]:
            lines.append("  • " + b)

    if extraction["business_model"]:
        lines.append(f"- Business model: {extraction['business_model']}")

    lines.append("\nMarket Summary:")
    if market.get("market_category"):
        lines.append(f"- Category: {market['market_category']}")
    if market.get("tam"):
        lines.append(f"- TAM: {market['tam']}")
    if market.get("growth_rate"):
        lines.append(f"- Growth: {market['growth_rate']}")

    if market.get("key_trends"):
        lines.append("- Trends:")
        for t in market["key_trends"]:
            lines.append("  • " + t)

    lines.append("\nFinancial Highlights:")
    for f in financial_bullets:
        lines.append("  • " + f)

    o = evaluation["overall"]
    lines.append("\nEvaluation Summary:")
    lines.append(f"- Score: {o['score']:.2f}/10")
    lines.append(f"- Verdict: {o['verdict']} (confidence {o['confidence']:.2f})")

    lines.append("- Strengths:")
    for s in evaluation["strengths"]:
        lines.append("  • " + s)

    lines.append("- Risks:")
    for r in evaluation["risks"]:
        lines.append("  • " + r)

    # pretty wrap
    wrapped = "\n".join([textwrap.fill(p, 90) for p in lines])
    return wrapped


class MemoAgent:
    def __init__(self, use_llm=False):
        self.use_llm = use_llm

    def evaluate(self, extracted, market, financial):
        # basic scoring (very simplified to keep stable)
        score = 6.5  # neutral baseline
        verdict = "Neutral"
        conf = 0.55

        # simple rule-based nudges
        if extracted.get("solution"):
            score += 0.5
        if market.get("tam"):
            score += 0.5
        if financial.get("summary", {}).get("revenue_monthly_start"):
            score += 0.5

        score = min(10, max(0, score))

        if score >= 7:
            verdict = "Invest"
            conf = 0.8
        elif score <= 5:
            verdict = "Avoid"
            conf = 0.4

        return {
            "overall": {
                "score": score,
                "verdict": verdict,
                "confidence": conf
            },
            "strengths": ["Good fundamentals."],
            "risks": ["Limited data; further validation required."]
        }

    def run(self, extracted, market, financial, explain=False):
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
            financial_bullets.append(f"Monthly revenue: {summary['revenue_monthly_start']}")
        if summary.get("gross_margin"):
            financial_bullets.append(f"Gross margin: {summary['gross_margin']*100:.1f}%")

        evaluation = self.evaluate(extracted, market, financial)

        memo_json = {
            "title": f"Investor Memo — {extraction['name']}",
            "sections": {
                "overview": extraction,
                "market": market_c,
                "financial": financial_bullets,
            },
            "evaluation": evaluation
        }

        memo_text = _memo_text(memo_json["title"], extraction, market_c, financial_bullets, evaluation)

        # LLM explanation optional
        llm_explanation = None
        if self.use_llm and explain:
            llm_explanation = {"note": "LLM explanation disabled in simplified mode."}

        return {
            "memo_json": memo_json,
            "memo_text": memo_text,
            "evaluation": evaluation,
            "llm_explanation": llm_explanation
        }
