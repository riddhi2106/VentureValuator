# agents/extractor_agent.py
import json
from typing import Optional

from agents.schemas import ExtractionOutput
from tools.llm_client import call_llm
from tools.pdf_reader import pdf_reader
from tools.startup_name import resolve_startup_name
from tools.structured_output import (
    StructuredOutputError,
    call_validated_json,
    extract_json_object,
)

# Slightly expanded prompt (keeps your original instructions but asks for extra numeric metrics)
DEFAULT_PROMPT_TEMPLATE = """
You are an expert startup analyst. Given the extracted raw text from a pitch deck or startup description below,
produce a JSON object with the following exact keys (use these exact key names):

- name  (the startup/company name — inspect the cover slide, logo text, headers, footers, and product references; REQUIRED)
- problem
- solution
- target_customer
- business_model
- pricing
- gtm_strategy
- team
- cost_structure
- competition
- notable_metrics
- assumptions
- evidence (object mapping each populated field to 1-3 short supporting fragments from the deck)

Return ONLY valid JSON.  
If you cannot find a value, set it to "" or [].
For "name": always return the best concise company or product name supported by the deck.
Never return "Unknown Startup", "Unknown", or a generic description.

NOTE: In notable_metrics extract numeric metrics when present, including revenue, MAU,
growth, retention, churn, gross margin, CAC, burn/monthly operating costs, NPS, repeat
rate, orders, and delivery metrics. Never invent missing metrics or assumptions.
Keep stated values exactly as written, including currency and time period. Put unsupported
interpretations in assumptions, never in notable_metrics. Evidence fragments must be short
and must come from the supplied text.

Raw text to analyze:
---
{raw_text}
"""

class ExtractionAgent:
    """
    LLM-backed extraction agent.
    Produces guaranteed clean JSON output.
    """

    def __init__(self, llm_preference: str = "chatgpt"):
        self.llm_preference = llm_preference

    def _safe_parse_json(self, resp_text: str) -> dict:
        """Extract JSON from an LLM response for backward-compatible callers."""

        return extract_json_object(resp_text)

    def extract_from_text(self, text: str, fallback_name: str | None = None) -> dict:
        prompt = DEFAULT_PROMPT_TEMPLATE.format(raw_text=text[:20000])
        print("[ExtractionAgent] Calling LLM...")

        try:
            validated = call_validated_json(
                prompt,
                ExtractionOutput,
                call_llm,
                attempts=2,
            )
            data = validated.model_dump()
        except StructuredOutputError as exc:
            print("[ExtractionAgent] Failed to parse JSON. Returning fallback template.")
            return {
                "name": resolve_startup_name(
                    {},
                    pdf_path=fallback_name,
                    raw_text=text,
                ),
                "problem": "",
                "solution": "",
                "target_customer": "",
                "business_model": "",
                "pricing": "",
                "gtm_strategy": "",
                "team": "",
                "cost_structure": "",
                "competition": [],
                "notable_metrics": {},
                "assumptions": "",
                "evidence": {},
                "missing_info": [],
                "raw_llm": exc.last_response,
                "validation_error": str(exc),
            }

        # REQUIRED KEYS
        required = [
            "name", "problem", "solution", "target_customer",
            "business_model", "pricing", "gtm_strategy",
            "team", "cost_structure", "competition", "notable_metrics", "assumptions"
        ]

        # === ADDED: attempt to canonicalize common metric keys and capture extra numeric fields ===
        # Do not remove any existing keys; only add normalized variants if missing.
        nm = data["notable_metrics"]

        def _copy_if_exists(src_keys, dest_key):
            for k in src_keys:
                if k in nm and nm.get(dest_key, "") == "":
                    nm[dest_key] = nm[k]

        # common alternate names mapping
        _copy_if_exists(["Last month revenue", "last_month_revenue", "revenue_last_month", "revenue (last month)"], "revenue_last_month")
        _copy_if_exists(["Monthly active users", "MAU", "mau"], "mau")
        _copy_if_exists(["Month-over-month growth", "MoM growth", "mom_growth"], "mom_growth")
        _copy_if_exists(["Net Promoter Score (NPS)", "NPS", "nps"], "nps")
        _copy_if_exists(["Repeat customers", "repeat_rate", "repeat"], "repeat_rate")
        _copy_if_exists(["Orders last quarter", "orders_last_quarter"], "orders_last_quarter")
        _copy_if_exists(["Number of hubs", "hubs", "number_of_hubs"], "number_of_hubs")
        _copy_if_exists(["COGS", "cogs", "cogs_percent"], "cogs_percent")
        _copy_if_exists(["avg_delivery_time", "average_delivery_time", "delivery_time_avg"], "avg_delivery_time")
        _copy_if_exists(["marketing_cost_monthly", "marketing_monthly"], "marketing_cost_monthly")
        _copy_if_exists(["tech_cost_monthly", "tech_monthly"], "tech_cost_monthly")
        _copy_if_exists(["gross_margin", "average_gross_margin"], "gross_margin")

        # If numeric strings exist but with extra text, keep as-is (downstream agents parse them).
        # For convenience, ensure the notable_metrics is a plain dict of simple values:
        for k, v in list(nm.items()):
            # convert small dicts to strings
            if isinstance(v, dict):
                try:
                    nm[k] = json.dumps(v)
                except (TypeError, ValueError):
                    nm[k] = str(v)

        # ensure every required key exists
        for key in required:
            if key not in data:
                if key == "competition":
                    data[key] = []
                elif key == "notable_metrics":
                    data[key] = {}
                elif key == "name":
                    data[key] = ""
                else:
                    data[key] = ""

        data["name"] = resolve_startup_name(
            data,
            pdf_path=fallback_name,
            raw_text=text,
        )

        # Track missing info fields
        data["missing_info"] = [k for k in required if not data.get(k)]

        print("[ExtractionAgent] Extraction complete.")
        return data

    def extract_from_pdf(self, pdf_path: str) -> dict:
        print("[ExtractionAgent] Reading PDF...")
        raw_text = pdf_reader(pdf_path)
        return self.extract_from_text(raw_text, fallback_name=pdf_path)

    def run(self, startup_text: Optional[str] = None, pdf_path: Optional[str] = None) -> dict:
        if pdf_path:
            return self.extract_from_pdf(pdf_path)
        if startup_text:
            return self.extract_from_text(startup_text)
        raise ValueError("Provide startup_text or pdf_path.")
