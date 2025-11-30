from typing import Dict, Any
import json
import os
from datetime import datetime
from tools.llm_client import call_gemini
from pptx import Presentation
from pptx.util import Pt


class PitchDeckAgent:
    """
    YC-style 12-slide deck generator.
    Produces both JSON slide structure AND a real .pptx file.
    """

    def __init__(self, model="models/gemini-2.5-flash"):
        self.model = model

    def _build_prompt(self, bundle: Dict[str, Any]):
        return f"""
You are a world-class YC-style investor and pitch deck designer.

Using the structured data below, create a **12-slide YC-style pitch deck**.
Do NOT invent financials or metrics. Use only what's provided.

FORMAT: Return ONLY JSON:
{{
  "slides": [
    {{"title": "Problem", "bullets": []}},
    {{"title": "Target User", "bullets": []}},
    {{"title": "Current Behavior", "bullets": []}},
    {{"title": "Solution", "bullets": []}},
    {{"title": "Why Now", "bullets": []}},
    {{"title": "Market Size", "bullets": []}},
    {{"title": "Competition", "bullets": []}},
    {{"title": "Unique Advantage", "bullets": []}},
    {{"title": "Business Model", "bullets": []}},
    {{"title": "Traction", "bullets": []}},
    {{"title": "Financial Projection Summary", "bullets": []}},
    {{"title": "The Ask (Fundraising)", "bullets": []}}
  ]
}}

========================
STARTUP DATA
========================
{json.dumps(bundle.get("extracted", {}), indent=2)}

========================
MARKET
========================
{json.dumps(bundle.get("market", {}), indent=2)}

========================
FINANCIALS
========================
{json.dumps(bundle.get("financial", {}), indent=2)}

========================
MEMO
========================
{json.dumps(bundle.get("memo", {}), indent=2)}
"""

    # ----------------------------------------------------------------------
    #   PPTX Creation Logic
    # ----------------------------------------------------------------------
    def _create_pptx(self, slides_json: Dict[str, Any], output_path=None):

        # Ensure output folder exists
        os.makedirs("outputs/decks", exist_ok=True)

        # Use timestamp-based filename unless specified
        if output_path is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"outputs/decks/pitch_deck_{ts}.pptx"

        prs = Presentation()

        for slide in slides_json["slides"]:
            layout = prs.slide_layouts[1]  # Title + body
            s = prs.slides.add_slide(layout)

            # Title
            s.shapes.title.text = slide["title"]

            # Body
            body = s.placeholders[1].text_frame
            body.clear()

            for bullet in slide["bullets"]:
                p = body.add_paragraph()
                p.text = str(bullet)
                p.level = 0
                p.font.size = Pt(20)

        prs.save(output_path)
        return output_path

    # ----------------------------------------------------------------------
    #   Main Run Logic
    # ----------------------------------------------------------------------
    def run(self, extracted, market, financial, memo):

        bundle = {
            "extracted": extracted,
            "market": market,
            "financial": financial,
            "memo": memo
        }

        prompt = self._build_prompt(bundle)
        raw = call_gemini(prompt, model=self.model)

        # Try to parse JSON safely
        try:
            slides_json = json.loads(raw)
        except Exception:
            # fallback: attempt substring JSON extraction
            try:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                slides_json = json.loads(raw[start:end])
            except Exception:
                return {"error": "Could not parse JSON", "raw": raw}

        # Generate PPTX
        pptx_path = self._create_pptx(slides_json)

        return {
            "slides_json": slides_json,
            "pptx_path": pptx_path
        }
