from typing import Dict, Any
from tools.llm_client import call_llm
from tools.web_search import search_for_startup
import json
import os


class MarketAgent:
    """
    Market research with optional web-grounded citations.
    """

    def __init__(self, use_web_search: bool = True):
        self.use_web_search = use_web_search

    def _build_prompt(self, extracted: Dict[str, Any], web_results: str = "", mcp_comps: str = ""):
        return f"""
You are a world-class startup market analyst.

Produce a STRUCTURED, FACT-BASED market research summary for the startup below.
When web research is provided, PRIORITIZE those findings for TAM, competitors, and trends.
Cite web sources in the "sources" array using their title and URL.

========================
STARTUP INFO (JSON)
========================
{json.dumps(extracted, indent=2)}

========================
WEB RESEARCH
========================
{web_results or "No web research available — use industry knowledge but flag uncertainty."}

========================
LIVE FINANCIAL COMPS (via MCP)
========================
{mcp_comps or "No live comps data retrieved."}

========================
REQUIRED OUTPUT (JSON FORMAT ONLY)
========================
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
  "summary_insights": "",
  "sources": [
    {{"title": "", "url": "", "snippet": ""}}
  ]
}}

GUIDELINES:
- Include at least 2 entries in "sources" when web research is available.
- Do NOT invent precise market numbers without basis — use ranges if uncertain.
- Keep JSON valid. Return ONLY the JSON object.
"""

    def _clean_json(self, text: str) -> str:
        clean = text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start != -1 and end > start:
            return clean[start:end]
        return clean

    def run(self, extracted: Dict[str, Any], search_tool=None) -> Dict[str, Any]:
        web_results = ""
        web_sources = []
        mcp_comps = ""

        use_search = self.use_web_search and os.getenv("DISABLE_WEB_SEARCH", "false").lower() not in ("true", "1")

        if use_search:
            try:
                if search_tool:
                    web_results, web_sources = search_tool(extracted)
                else:
                    web_results, web_sources = search_for_startup(extracted)
            except Exception as e:
                web_results = f"Web search failed: {e}"

        # Fetch live comps via MCP
        try:
            from tools.mcp_client import get_public_comps
            # We'll do a quick check to see if we can find a related public tech company ticker
            # For hackathon demo purposes, we will default to "SNOW" (Snowflake) if it's SaaS, or "AAPL" if hardware.
            # Ideally this would be dynamically extracted.
            biz = str(extracted.get("business_model", "")).lower()
            ticker = "AAPL"
            if "saas" in biz or "software" in biz:
                ticker = "SNOW"
            if "ai" in str(extracted.get("solution", "")).lower():
                ticker = "NVDA"
                
            mcp_comps = get_public_comps(ticker)
        except Exception as e:
            mcp_comps = f"MCP comps failed: {e}"

        prompt = self._build_prompt(extracted, web_results, mcp_comps)
        resp_text = call_llm(prompt)
        clean_json = self._clean_json(resp_text)

        try:
            data = json.loads(clean_json)
        except Exception as e:
            return {
                "error": "Failed to parse JSON",
                "exception": str(e),
                "raw_response": resp_text,
                "cleaned_response": clean_json,
            }

        # Merge web sources if LLM didn't include them
        llm_sources = data.get("sources") or []
        if web_sources and len(llm_sources) < 2:
            existing_urls = {s.get("url") for s in llm_sources if s.get("url")}
            for src in web_sources:
                if src.get("url") and src["url"] not in existing_urls:
                    llm_sources.append({
                        "title": src.get("title", ""),
                        "url": src.get("url", ""),
                        "snippet": src.get("snippet", ""),
                    })
            data["sources"] = llm_sources[:8]

        data["web_search_used"] = use_search and bool(web_sources)
        return data
