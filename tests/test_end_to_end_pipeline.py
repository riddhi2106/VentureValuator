import agents.extractor_agent as extractor_module
import agents.market_agent as market_module
import core.orchestrator as orchestrator
import tools.mcp_client as mcp_client
from agents.deck_agent import PitchDeckAgent


class _Memory:
    def __init__(self):
        self.runs = []
        self.summaries = []

    def add_run(self, result):
        self.runs.append(result)

    def append_to_memory_bank(self, summary):
        self.summaries.append(summary)


def test_full_pipeline_runs_real_agents_with_external_boundaries_mocked(
    monkeypatch,
    tmp_path,
):
    """Exercise extraction through memo/deck output without network or credentials."""

    memory = _Memory()
    progress = []
    output_path = tmp_path / "venturevaluator.pptx"

    monkeypatch.setenv("TEST_MODE", "true")
    monkeypatch.setenv("DISABLE_WEB_SEARCH", "false")
    monkeypatch.setattr(
        extractor_module,
        "pdf_reader",
        lambda path: "VentureValuator automates startup pitch-deck diligence.",
    )
    monkeypatch.setattr(
        market_module,
        "search_for_startup",
        lambda extracted: (
            "Grounded market evidence",
            [
                {
                    "title": "Venture software market",
                    "url": "https://example.com/venture-market",
                    "snippet": "Market evidence",
                }
            ],
        ),
    )
    monkeypatch.setattr(mcp_client, "get_public_comps", lambda ticker: "Comparable P/S: 8x")
    monkeypatch.setattr(
        PitchDeckAgent,
        "_create_pptx",
        lambda self, slides_json: str(output_path),
    )
    monkeypatch.setattr(orchestrator, "memory", memory)

    result = orchestrator.run_full_analysis(
        str(tmp_path / "venturevaluator.pdf"),
        progress_callback=lambda step, label, phase, error=None: progress.append(
            (step, phase, error)
        ),
    )

    assert result["extracted"]["name"] == "VentureValuator"
    assert result["market"]["market_category"] == "AI Productivity Software / Venture Intelligence"
    assert result["financial_model"]["summary"]["revenue_monthly_start"] == 12_000
    assert result["skeptic"]["red_flags"]
    assert 0 <= result["memo"]["evaluation"]["overall"]["score"] <= 10
    assert len(result["deck_raw"]["slides_json"]["slides"]) == 12
    assert result["deck"] == str(output_path)
    assert memory.runs == [result]
    assert memory.summaries[0]["name"] == "VentureValuator"
    assert [step for step, phase, _ in progress if phase == "done"] == [
        "extraction",
        "market",
        "financial",
        "skeptic",
        "memo",
        "deck",
    ]
