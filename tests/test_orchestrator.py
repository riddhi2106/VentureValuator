import pytest

import core.orchestrator as orchestrator


class _Extractor:
    def run(self, pdf_path):
        return {"name": "Acme", "solution": "Automation", "notable_metrics": {}}


class _Market:
    def __init__(self, use_web_search=True):
        self.use_web_search = use_web_search

    def run(self, extracted):
        return {"market_category": "Software", "tam": "$1B"}


class _Financial:
    def run(self, extracted):
        return {"summary": {}, "scenarios": {"base": {}}}


class _Skeptic:
    def run(self, extracted, market, financial):
        return {"red_flags": []}


class _Memo:
    def __init__(self, use_llm=True):
        self.use_llm = use_llm

    def run(self, extracted, market, financial, skeptic):
        return {
            "evaluation": {
                "overall": {"score": 6.5, "verdict": "Pass", "confidence": 0.7}
            }
        }


class _Deck:
    def run(self, extracted, market, financial, memo):
        return {"pptx_path": "/tmp/acme.pptx"}


class _Memory:
    def __init__(self):
        self.runs = []
        self.bank = []

    def add_run(self, result):
        self.runs.append(result)

    def append_to_memory_bank(self, summary):
        self.bank.append(summary)


def _patch_pipeline(monkeypatch):
    memory = _Memory()
    monkeypatch.setattr(orchestrator, "ExtractionAgent", _Extractor)
    monkeypatch.setattr(orchestrator, "MarketAgent", _Market)
    monkeypatch.setattr(orchestrator, "FinancialAgent", _Financial)
    monkeypatch.setattr(orchestrator, "SkepticAgent", _Skeptic)
    monkeypatch.setattr(orchestrator, "MemoAgent", _Memo)
    monkeypatch.setattr(orchestrator, "PitchDeckAgent", _Deck)
    monkeypatch.setattr(orchestrator, "memory", memory)
    return memory


def test_orchestrator_runs_all_steps_and_persists_result(monkeypatch):
    memory = _patch_pipeline(monkeypatch)
    progress = []

    result = orchestrator.run_full_analysis(
        "/tmp/acme.pdf",
        progress_callback=lambda step, label, phase, error=None: progress.append(
            (step, phase, error)
        ),
    )

    assert result["extracted"]["name"] == "Acme"
    assert result["deck"] == "/tmp/acme.pptx"
    assert [item[0] for item in progress if item[1] == "done"] == [
        "extraction",
        "market",
        "financial",
        "skeptic",
        "memo",
        "deck",
    ]
    assert memory.runs == [result]
    assert memory.bank[0]["name"] == "Acme"


def test_orchestrator_honors_cancellation_before_first_step(monkeypatch):
    _patch_pipeline(monkeypatch)
    progress = []

    with pytest.raises(orchestrator.PipelineCancelledError):
        orchestrator.run_full_analysis(
            "/tmp/acme.pdf",
            cancel_check=lambda: True,
            progress_callback=lambda step, label, phase, error=None: progress.append(
                (step, phase, error)
            ),
        )

    assert progress == [("extraction", "error", "Cancelled by user")]

