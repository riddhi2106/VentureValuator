# agents/impact_agent.py
import json
from typing import Dict, Any
from tools.llm_client import call_gemini

class ImpactAgent:
    """
    Impact Scoring Agent using Gemini ADK capabilities.
    Evaluates how well a startup addresses UN Sustainable Development Goals (SDGs),
    specifically targeting Rural Health, Waste, and Traffic.
    """

    def __init__(self):
        pass

    def _build_prompt(self, extracted: Dict[str, Any]) -> str:
        return f"""
You are an expert Impact Assessor evaluating startups against UN Sustainable Development Goals (SDGs).
Your task is to analyze the following startup and determine its impact on Rural Health, Waste Management, or Traffic/Urban Mobility.

========================
STARTUP INFO (JSON)
========================
{json.dumps(extracted, indent=2)}

========================
REQUIRED OUTPUT (JSON FORMAT ONLY)
========================
{{
  "sdg_alignment": "",
  "impact_score": 0.0,
  "rationale": "",
  "metrics_to_track": []
}}

GUIDELINES:
- "sdg_alignment": Which specific SDG or category (Rural Health, Waste, Traffic) does this address most directly?
- "impact_score": A score from 0.0 to 10.0 representing the potential positive impact. (Use 0 if completely irrelevant to these areas).
- "rationale": A brief explanation of the score.
- "metrics_to_track": 2-3 specific KPIs that should be monitored to verify impact (e.g., "tons of CO2 reduced", "patients served in rural clinics").
- Return ONLY valid JSON.
"""

    def _clean_json(self, text: str) -> str:
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start != -1 and end > start:
            return clean[start:end]
        return clean

    def run(self, extracted: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(extracted)
        print("[ImpactAgent] Calling Gemini ADK for impact assessment...")
        
        resp_text = call_gemini(prompt)
        clean_json = self._clean_json(resp_text)

        try:
            data = json.loads(clean_json)
        except Exception as e:
            return {
                "sdg_alignment": "Unknown",
                "impact_score": 0.0,
                "rationale": "Failed to parse JSON response from Gemini.",
                "metrics_to_track": [],
                "error": str(e)
            }

        return data
