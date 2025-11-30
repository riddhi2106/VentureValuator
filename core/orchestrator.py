from agents.extractor_agent import ExtractionAgent
from agents.market_agent import MarketAgent
from agents.financial_agent import FinancialAgent
from agents.memo_agent import MemoAgent
from agents.deck_agent import PitchDeckAgent

from core.memory_manager import memory
from datetime import datetime
import json


def run_full_analysis(pdf_path: str):
    print("\n🚀 Starting VentureValuator analysis pipeline...\n")

    # Instantiate agents
    extractor = ExtractionAgent()
    market_agent = MarketAgent()
    financial_agent = FinancialAgent()
    memo_agent = MemoAgent()
    deck_agent = PitchDeckAgent()

    # 1. Extraction
    print("📄 Extracting pitch data from PDF...")
    extracted = extractor.run(pdf_path=pdf_path)
    print("\n=== DEBUG: Extracted Data ===")
    print(json.dumps(extracted, indent=2))
    print("=============================\n")
    print("✓ Extraction complete\n")

    # 2. Market Research
    print("🌍 Running market analysis...")
    market_data = market_agent.run(extracted)
    print("✓ Market research complete\n")

    # 3. Financial Modeling
    print("📊 Building financial model...")
    financial_model = financial_agent.run(extracted)
    print("✓ Financial modeling complete\n")

    # 4. Memo Generation
    print("📝 Generating investor memo...")
    memo_output = memo_agent.run(extracted, market_data, financial_model)
    print("✓ Investor memo generated\n")

    # 5. Pitch Deck Generation
    print("📑 Creating pitch deck...")
    deck_output = deck_agent.run(extracted, market_data, financial_model, memo_output)
    print("✓ Pitch deck created\n")

    pptx_path = deck_output.get("pptx_path", None)

    # Final combined result
    result = {
    "timestamp": str(datetime.now()),
    "pdf_path": pdf_path,
    "extracted": extracted,
    "market": market_data,
    "financial_model": financial_model,
    "memo": memo_output,
    "deck": pptx_path,
    "deck_raw": deck_output
}

    # -------------------------------
    # 🧠 SAVE MEMORY (new system)
    # -------------------------------

    # Save full run
    memory.add_run(result)

    # Add compact summary to long-term bank
    memory.append_to_memory_bank({
        "timestamp": result["timestamp"],
        "name": extracted.get("name", "Unknown Startup"),
        "one_liner": extracted.get("solution", "")[:150],
        "market_category": market_data.get("market_category", ""),
        "tam": market_data.get("tam", ""),
        "mau": extracted.get("notable_metrics", {}).get("Monthly active users", None),
        "revenue": extracted.get("notable_metrics", {}).get("Last month revenue", None)
    })

    print("🎉 VentureValuator analysis complete!\n")
    print("📌 Session saved in memory.")
    print("📌 Summary added to long-term memory.\n")

    return result
