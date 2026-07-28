from agents.extractor_agent import ExtractionAgent
from agents.market_agent import MarketAgent
from agents.financial_agent import FinancialAgent
from agents.skeptic_agent import SkepticAgent
from agents.memo_agent import MemoAgent
from agents.deck_agent import PitchDeckAgent

from core.memory_manager import memory
from datetime import datetime
from typing import Callable, Optional
from tools.startup_name import resolve_startup_name


class PipelineStepError(Exception):
    def __init__(self, step: str, label: str, message: str):
        self.step = step
        self.label = label
        super().__init__(message)


class PipelineCancelledError(Exception):
    """Raised when the user stops the pipeline between steps."""

    def __init__(self, step: str, label: str):
        self.step = step
        self.label = label
        super().__init__(f"Analysis stopped before completing: {label}")


CancelCheck = Callable[[], bool]
ProgressCallback = Callable[[str, str, str, Optional[str]], None]


def _notify(callback: Optional[ProgressCallback], step: str, label: str, phase: str, error: str = None):
    if callback:
        callback(step, label, phase, error)


def _check_cancel(
    cancel_check: Optional[CancelCheck],
    step_key: str,
    label: str,
    progress_callback: Optional[ProgressCallback] = None,
):
    if cancel_check and cancel_check():
        _notify(progress_callback, step_key, label, "error", "Cancelled by user")
        raise PipelineCancelledError(step_key, label)


def run_full_analysis(
    pdf_path: str,
    progress_callback: Optional[ProgressCallback] = None,
    cancel_check: Optional[CancelCheck] = None,
):
    extractor = ExtractionAgent()
    market_agent = MarketAgent(use_web_search=True)
    financial_agent = FinancialAgent()
    skeptic_agent = SkepticAgent()
    memo_agent = MemoAgent(use_llm=True)
    deck_agent = PitchDeckAgent()

    steps = [
        ("extraction", "Extracting pitch data from PDF", lambda: extractor.run(pdf_path=pdf_path)),
        ("market", "Running web-grounded market research", lambda ctx: market_agent.run(ctx["extracted"])),
        ("financial", "Building financial model", lambda ctx: financial_agent.run(ctx["extracted"])),
        ("skeptic", "Skeptical VC review", lambda ctx: skeptic_agent.run(ctx["extracted"], ctx["market"], ctx["financial"])),
        ("memo", "Generating investor memo & score", lambda ctx: memo_agent.run(ctx["extracted"], ctx["market"], ctx["financial"], ctx["skeptic"])),
        ("deck", "Creating pitch deck", lambda ctx: deck_agent.run(ctx["extracted"], ctx["market"], ctx["financial"], ctx["memo"])),
    ]

    ctx = {}

    for step_key, label, fn in steps:
        _check_cancel(cancel_check, step_key, label, progress_callback)
        _notify(progress_callback, step_key, label, "start")
        try:
            if step_key == "extraction":
                ctx["extracted"] = fn()
            elif step_key == "market":
                ctx["market"] = fn(ctx)
            elif step_key == "financial":
                ctx["financial"] = fn(ctx)
            elif step_key == "skeptic":
                ctx["skeptic"] = fn(ctx)
            elif step_key == "memo":
                ctx["memo"] = fn(ctx)
            elif step_key == "deck":
                ctx["deck_output"] = fn(ctx)
        except Exception as e:
            _notify(progress_callback, step_key, label, "error", str(e))
            raise PipelineStepError(step_key, label, str(e)) from e
        _notify(progress_callback, step_key, label, "done")

    deck_output = ctx["deck_output"]
    extracted = ctx["extracted"]
    market_data = ctx["market"]
    financial_model = ctx["financial"]
    skeptic_output = ctx["skeptic"]
    memo_output = ctx["memo"]
    pptx_path = deck_output.get("pptx_path")

    result = {
        "timestamp": str(datetime.now()),
        "pdf_path": pdf_path,
        "extracted": extracted,
        "market": market_data,
        "financial_model": financial_model,
        "skeptic": skeptic_output,
        "memo": memo_output,
        "deck": pptx_path,
        "deck_raw": deck_output,
    }

    memory.add_run(result)

    solution = extracted.get("solution", "")
    one_liner = solution[:150] if isinstance(solution, str) else str(solution)[:150]

    memory.append_to_memory_bank({
        "timestamp": result["timestamp"],
        "name": resolve_startup_name(extracted, pdf_path=pdf_path),
        "one_liner": one_liner,
        "market_category": market_data.get("market_category", ""),
        "tam": market_data.get("tam", ""),
        "score": memo_output.get("evaluation", {}).get("overall", {}).get("score"),
        "verdict": memo_output.get("evaluation", {}).get("overall", {}).get("verdict"),
        "mau": (
            extracted.get("notable_metrics", {}).get("mau")
            or extracted.get("notable_metrics", {}).get("Monthly active users")
        ),
        "revenue": (
            extracted.get("notable_metrics", {}).get("revenue_last_month")
            or extracted.get("notable_metrics", {}).get("Last month revenue")
        ),
    })

    return result
