from typing import Dict, Any
from tools.llm_client import call_gemini
import json
import re

class MarketAgent:
    """
    MarketResearchAgent takes structured extraction output and produces:
    - Market size (TAM/SAM/SOM)
    - Growth estimates
    - Competitor landscape
    - Opportunities & risks
    - Industry-specific benchmarks
    - Regional factors
    - Summary insights
    """

    def __init__(self, use_web_search: bool = False):
        self.use_web_search = use_web_search

    def _build_prompt(self, extracted: Dict[str, Any], web_results: str = ""):
        return f"""
You are a world-class startup market analyst.

Your task: Produce a STRUCTURED, FACT-BASED market research summary 
for the startup described below.

========================
STARTUP INFO (JSON)
========================
{json.dumps(extracted, indent=2)}

========================
WEB RESEARCH (optional)
========================
{web_results}

========================
REQUIRED OUTPUT (JSON FORMAT ONLY)
========================
Respond ONLY with valid JSON containing the keys below:

{{
  "market_category": "",
  "tam": "",
  "sam": "",
  "som": "",
  "market_growth_rate": "",
  "key_trends": [],
  "customer_segments": [],
  "competitive_landscape": {{
      "direct_competitors": [],
      "indirect_competitors": [],
      "competitive_advantages": [],
      "competitive_risks": []
  }},
  "regional_factors": "",
  "industry_benchmarks": {{
      "average_gross_margin": "",
      "typical_cac_range": "",
      "ltv_range": "",
      "unit_economics_notes": ""
  }},
  "opportunities": [],
  "risks": [],
  "summary_insights": ""
}}

========================
GUIDELINES
========================
- Pull factual market patterns from your training. 
- If numbers vary, give typical industry ranges.
- Do NOT hallucinate precise financial numbers unless the industry has known estimates.
- Keep the JSON valid.
"""

    def _clean_json(self, text: str) -> str:
        """Remove markdown code fences (```json ... ```)."""
        clean = text.replace("```json", "").replace("```", "").strip()
        return clean

    def run(self, extracted: Dict[str, Any], search_tool=None) -> Dict[str, Any]:
        """
        Main entrypoint.
        If use_web_search=True, will call search_tool(query) to enrich results.
        """

        web_results = ""

        if self.use_web_search and search_tool:
            industry = extracted.get("industry") or extracted.get("Industry") or ""
            location = extracted.get("location") or extracted.get("Location") or ""

            queries = [
                f"{industry} market size {location}",
                f"{industry} competitors India",
                f"{industry} growth rate report",
                f"{industry} trends 2025"
            ]

            combined_results = []
            for q in queries:
                try:
                    search_output = search_tool(q)
                    combined_results.append(f"Query: {q}\nResult:\n{search_output}\n")
                except Exception as e:
                    combined_results.append(f"Query: {q}\nError: {e}")

            web_results = "\n".join(combined_results)

        # Build the prompt
        prompt = self._build_prompt(extracted, web_results)

        # Call Gemini
        resp_text = call_gemini(prompt, model="models/gemini-2.5-flash")

        # Clean markdown code fences
        clean_json = self._clean_json(resp_text)

        # Parse JSON safely
        try:
            return json.loads(clean_json)
        except Exception as e:
            return {
                "error": "Failed to parse JSON",
                "exception": str(e),
                "raw_response": resp_text,
                "cleaned_response": clean_json
            }
