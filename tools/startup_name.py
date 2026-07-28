"""Helpers for producing a useful startup title from analysis inputs."""

from __future__ import annotations

import os
import re
from typing import Any


_PLACEHOLDER_NAMES = {
    "",
    "unknown",
    "unknown startup",
    "startup",
    "startup analysis",
    "n/a",
    "none",
}

_GENERIC_TEXT_LINES = {
    "pitch deck",
    "investor presentation",
    "confidential",
    "problem",
    "solution",
    "company overview",
}


def is_placeholder_startup_name(value: Any) -> bool:
    return not isinstance(value, str) or value.strip().casefold() in _PLACEHOLDER_NAMES


def _clean_candidate(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" \t\r\n|•·–—:-")
    return value[:80].strip()


def infer_name_from_text(text: str) -> str | None:
    """Use an early cover-page line when the model did not return a name."""
    for raw_line in text.splitlines()[:40]:
        candidate = _clean_candidate(raw_line)
        lowered = candidate.casefold()
        if (
            2 <= len(candidate) <= 60
            and any(char.isalpha() for char in candidate)
            and lowered not in _GENERIC_TEXT_LINES
            and not lowered.startswith(("http://", "https://", "www."))
            and not re.match(r"^(problem|solution|market|traction|team)\b", lowered)
        ):
            return candidate
    return None


def name_from_pdf_path(pdf_path: str | None) -> str | None:
    if not pdf_path:
        return None
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    candidate = _clean_candidate(re.sub(r"[_-]+", " ", stem))
    return candidate or None


def resolve_startup_name(
    extracted: dict[str, Any] | None,
    *,
    pdf_path: str | None = None,
    raw_text: str | None = None,
) -> str:
    extracted = extracted or {}
    for key in ("name", "company_name"):
        candidate = extracted.get(key)
        if not is_placeholder_startup_name(candidate):
            return _clean_candidate(candidate)

    if raw_text:
        text_name = infer_name_from_text(raw_text)
        if text_name:
            return text_name

    file_name = name_from_pdf_path(pdf_path)
    if file_name:
        return file_name

    return "Startup Analysis"
