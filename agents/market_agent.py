import json
from typing import Any, Dict

from agents.schemas import MarketOutput
from core.config import get_settings
from tools.llm_client import call_llm
from tools.structured_output import StructuredOutputError, call_validated_json
from tools.web_search import search_for_startup

COMPARABLE_RULES = (
    (("health", "clinical", "pharma"), "VEEV", "vertical healthcare software"),
    (("fintech", "payment", "banking"), "SQ", "digital payments and fintech"),
    (("cybersecurity", "security"), "CRWD", "cloud cybersecurity"),
    (("marketplace", "ecommerce", "commerce"), "AMZN", "digital commerce marketplace"),
    (("data platform", "cloud data", "warehouse"), "SNOW", "cloud data platform"),
    (("hardware", "device", "consumer electronics"), "AAPL", "technology hardware"),
    (
        ("artificial intelligence", "machine learning", "ai-powered", " ai "),
        "NVDA",
        "AI infrastructure",
    ),
    (("saas", "software"), "CRM", "horizontal SaaS"),
)


class MarketAgent:
    """
    Market research with optional web-grounded citations.
    """

    def __init__(self, use_web_search: bool = True):
        self.use_web_search = use_web_search

    def _select_public_comparable(self, extracted: Dict[str, Any]) -> tuple[str, str] | None:
        """Select a transparent broad public comparable from startup keywords.

        The comparable is contextual evidence, not a valuation recommendation.
        Returning ``None`` is preferable to silently defaulting an unrelated
        startup to a consumer-hardware company.
        """

        haystack = f" {str(extracted).lower()} "
        for keywords, ticker, rationale in COMPARABLE_RULES:
            if any(keyword in haystack for keyword in keywords):
                return ticker, rationale
        return None

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
- Distinguish startup-specific evidence from broad public-comparable context.
- If a claim is unsupported, leave it blank or explicitly describe the uncertainty.
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

        use_search = self.use_web_search and not get_settings().disable_web_search

        if use_search:
            try:
                if search_tool:
                    web_results, web_sources = search_tool(extracted)
                else:
                    web_results, web_sources = search_for_startup(extracted)
            except Exception as e:
                web_results = f"Web search failed: {e}"

        comparable = self._select_public_comparable(extracted)
        comparable_meta = None
        try:
            from tools.mcp_client import get_public_comps

            if comparable:
                ticker, rationale = comparable
                comparable_data = get_public_comps(ticker)
                mcp_comps = (
                    f"Ticker: {ticker}\n"
                    f"Selection rationale: {rationale}\n"
                    f"Comparable data: {comparable_data}"
                )
                comparable_meta = {
                    "ticker": ticker,
                    "selection_rationale": rationale,
                    "data": comparable_data,
                }
            else:
                mcp_comps = "No sufficiently relevant public comparable selected."
        except Exception as e:
            mcp_comps = f"MCP comps failed: {e}"

        prompt = self._build_prompt(extracted, web_results, mcp_comps)
        try:
            data = call_validated_json(
                prompt,
                MarketOutput,
                call_llm,
                attempts=2,
            ).model_dump()
        except StructuredOutputError as exc:
            return {
                "error": "Failed to parse JSON",
                "exception": str(exc),
                "raw_response": exc.last_response,
            }

        # Always reconcile the model's citations with sources actually returned
        # by research. This prevents a plausible-looking invented URL from
        # receiving the same confidence credit as a retrieved source.
        llm_sources = data.get("sources") or []
        researched_urls = {source.get("url") for source in web_sources if source.get("url")}
        for source in llm_sources:
            source["verified"] = bool(source.get("url") in researched_urls)
        if web_sources:
            existing_urls = {source.get("url") for source in llm_sources if source.get("url")}
            for src in web_sources:
                if src.get("url") and src["url"] not in existing_urls:
                    llm_sources.append({
                        "title": src.get("title", ""),
                        "url": src.get("url", ""),
                        "snippet": src.get("snippet", ""),
                        "verified": True,
                    })
            data["sources"] = llm_sources[:8]

        data["web_search_used"] = use_search and bool(web_sources)
        data["source_validation"] = {
            "researched_urls": len(researched_urls),
            "verified_citations": sum(
                1 for source in data.get("sources", []) if source.get("verified")
            ),
        }
        data["public_comparable"] = comparable_meta
        return data
