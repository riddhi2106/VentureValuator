import json
from typing import Any, Dict

from tools.llm_client import call_llm


class SkepticAgent:
    """
    Skeptical VC partner agent — challenges claims, flags gaps,
    and generates questions for a partner meeting.
    """

    def _build_prompt(
        self,
        extracted: Dict[str, Any],
        market: Dict[str, Any],
        financial: Dict[str, Any],
    ) -> str:
        return f"""
You are a skeptical Series A partner at a top-tier VC firm. Your job is NOT to be encouraging —
you stress-test this pitch deck like you would in a Monday partner meeting.

Review the extraction, market research, and financial model below. Be specific and cite actual
gaps from the data (missing metrics, vague TAM, weak moat, etc.).

========================
EXTRACTED PITCH DATA
========================
{json.dumps(extracted, indent=2)}

========================
MARKET RESEARCH
========================
{json.dumps(market, indent=2)}

========================
FINANCIAL MODEL
========================
{json.dumps(financial, indent=2)}

========================
REQUIRED OUTPUT (JSON ONLY)
========================
{{
  "red_flags": ["specific concern citing deck data"],
  "missing_data": ["metric or info not provided but required for diligence"],
  "challenged_claims": ["claim from deck that needs verification and why"],
  "partner_questions": ["sharp question you'd ask the founder in a meeting"],
  "diligence_next_steps": ["what you'd verify before writing a term sheet"],
  "skeptic_summary": "2-3 sentence blunt assessment"
}}

GUIDELINES:
- Be direct and specific — no generic VC platitudes.
- Reference actual fields from the data (TAM, revenue, competition, etc.).
- If data is missing, say so explicitly.
- Return ONLY valid JSON.
"""

    def _clean_json(self, text: str) -> str:
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start != -1 and end > start:
            return clean[start:end]
        return clean

    def run(
        self,
        extracted: Dict[str, Any],
        market: Dict[str, Any],
        financial: Dict[str, Any],
    ) -> Dict[str, Any]:
        prompt = self._build_prompt(extracted, market, financial)
        resp_text = call_llm(prompt)
        clean = self._clean_json(resp_text)

        try:
            return json.loads(clean)
        except Exception as e:
            return {
                "error": "Failed to parse skeptic JSON",
                "exception": str(e),
                "raw_response": resp_text,
            }
