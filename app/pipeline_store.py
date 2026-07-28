"""Thread-safe pipeline state for background worker threads."""

from __future__ import annotations

import threading
from typing import Any


class PipelineStore:
    """Shared state between the pipeline worker thread and Streamlit reruns."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = False
        self.cancel_requested = False
        self.progress: dict[str, dict[str, Any]] = {}
        self.result: dict | None = None
        self.error: str | None = None
        self.show_results = False

    def begin(self) -> None:
        with self._lock:
            self.running = True
            self.cancel_requested = False
            self.progress = {}
            self.result = None
            self.error = None
            self.show_results = False

    def request_cancel(self) -> None:
        with self._lock:
            self.cancel_requested = True

    def is_cancel_requested(self) -> bool:
        with self._lock:
            return self.cancel_requested

    def update_progress(self, step: str, label: str, phase: str, error: str | None = None) -> None:
        with self._lock:
            self.progress[step] = {"label": label, "phase": phase, "error": error}

    def finish_success(self, result: dict) -> None:
        with self._lock:
            self.result = result
            self.show_results = True
            self.error = None
            self.running = False
            self.cancel_requested = False

    def finish_cancelled(self, message: str) -> None:
        with self._lock:
            self.error = message
            self.show_results = False
            self.running = False
            self.cancel_requested = False

    def finish_error(self, message: str) -> None:
        with self._lock:
            self.error = message
            self.running = False
            self.cancel_requested = False

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": self.running,
                "cancel_requested": self.cancel_requested,
                "progress": dict(self.progress),
                "result": self.result,
                "error": self.error,
                "show_results": self.show_results,
            }


pipeline_store = PipelineStore()
