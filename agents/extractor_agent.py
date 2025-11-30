# agents/extractor_agent.py
import json
from typing import Optional
from tools.pdf_reader import pdf_reader
from tools.llm_client import call_gemini

# Slightly expanded prompt (keeps your original instructions but asks for extra numeric metrics)
DEFAULT_PROMPT_TEMPLATE = """
You are an expert startup analyst. Given the extracted raw text from a pitch deck or startup description below,
produce a JSON object with the following exact keys (use these exact key names):

- problem
- solution
- target_customer
- business_model
- pricing
- gtm_strategy
- cost_structure
- competition
- notable_metrics
- assumptions

Return ONLY valid JSON.  
If you cannot find a value, set it to "" or [].

NOTE (ADDED): In notable_metrics try to extract any numeric metrics if present (examples: Last month revenue, MAU, MoM growth, NPS, repeat rate, orders last quarter, number of hubs, COGS %, marketing_cost_monthly, tech_cost_monthly, avg_delivery_time). Put them inside the notable_metrics dict with reasonable keys.

Raw text to analyze:
---
{raw_text}
"""

class ExtractionAgent:
    """
    Extraction agent using Gemini.
    Produces guaranteed clean JSON output.
    """

    def __init__(self, llm_preference: str = "gemini"):
        self.llm_preference = llm_preference

    def _safe_parse_json(self, resp_text: str) -> dict:
        """
        Safely extract JSON even if Gemini returns markdown fences or text around it.
        """
        clean = resp_text.replace("```json", "").replace("```", "").strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON object found in LLM response.")

        return json.loads(clean[start:end])

    def extract_from_text(self, text: str) -> dict:
        prompt = DEFAULT_PROMPT_TEMPLATE.format(raw_text=text[:20000])
        print("[ExtractionAgent] Calling LLM...")

        resp_text = call_gemini(prompt, model="models/gemini-2.5-flash")

        # Parse JSON safely
        try:
            data = self._safe_parse_json(resp_text)
        except Exception:
            print("[ExtractionAgent] Failed to parse JSON. Returning fallback template.")
            return {
                "problem": "",
                "solution": "",
                "target_customer": "",
                "business_model": "",
                "pricing": "",
                "gtm_strategy": "",
                "cost_structure": "",
                "competition": [],
                "notable_metrics": {},
                "assumptions": "",
                "missing_info": [],
                "raw_llm": resp_text
            }

        # REQUIRED KEYS
        required = [
            "problem", "solution", "target_customer",
            "business_model", "pricing", "gtm_strategy",
            "cost_structure", "competition", "notable_metrics", "assumptions"
        ]

        # --- TYPE NORMALIZATION FIXES ----

        # competition must be list
        if isinstance(data.get("competition"), str):
            data["competition"] = [data["competition"]] if data["competition"] else []
        if data.get("competition") is None:
            data["competition"] = []

        # notable_metrics must be dict
        if isinstance(data.get("notable_metrics"), str):
            try:
                data["notable_metrics"] = json.loads(data["notable_metrics"])
            except Exception:
                data["notable_metrics"] = {}
        if data.get("notable_metrics") is None:
            data["notable_metrics"] = {}

        # --- Normalize notable_metrics if it's a LIST ---
        if isinstance(data.get("notable_metrics"), list):
            cleaned = {}
            for item in data["notable_metrics"]:
                # Parse "Key: Value" style strings
                if isinstance(item, str) and ":" in item:
                    key, val = item.split(":", 1)
                    cleaned[key.strip()] = val.strip()
                # If the list contains small dicts, merge them
                elif isinstance(item, dict):
                    for kk, vv in item.items():
                        cleaned[str(kk).strip()] = vv
            # If we parsed something, use it; else fallback to empty dict
            data["notable_metrics"] = cleaned if cleaned else {}

        if data.get("notable_metrics") is None:
            data["notable_metrics"] = {}

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
                except:
                    nm[k] = str(v)

        # ensure every required key exists
        for key in required:
            if key not in data:
                if key == "competition":
                    data[key] = []
                elif key == "notable_metrics":
                    data[key] = {}
                else:
                    data[key] = ""

        # Track missing info fields
        data["missing_info"] = [k for k in required if not data.get(k)]

        print("[ExtractionAgent] Extraction complete.")
        return data

    def extract_from_pdf(self, pdf_path: str) -> dict:
        print("[ExtractionAgent] Reading PDF...")
        raw_text = pdf_reader(pdf_path)
        return self.extract_from_text(raw_text)

    def run(self, startup_text: Optional[str] = None, pdf_path: Optional[str] = None) -> dict:
        if pdf_path:
            return self.extract_from_pdf(pdf_path)
        if startup_text:
            return self.extract_from_text(startup_text)
        raise ValueError("Provide startup_text or pdf_path.")
