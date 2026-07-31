"""Reusable validation and bounded-retry support for LLM JSON responses."""

import json
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)


class StructuredOutputError(ValueError):
    """Raised after an LLM repeatedly returns invalid structured output."""

    def __init__(self, message: str, *, last_response: str = ""):
        self.last_response = last_response
        super().__init__(message)


def extract_json_object(text: str) -> dict:
    """Extract the outermost JSON object from plain text or a Markdown fence."""

    clean = text.replace("```json", "").replace("```", "").strip()
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    value = json.loads(clean[start:end])
    if not isinstance(value, dict):
        raise ValueError("Model response must contain a JSON object")
    return value


def call_validated_json(
    prompt: str,
    schema: type[ModelT],
    call: Callable[[str], str],
    *,
    attempts: int = 2,
) -> ModelT:
    """Call an LLM until its JSON validates against ``schema`` or retries expire.

    The correction prompt includes only the validation error, not application
    secrets or hidden state. Two attempts balance resilience with token cost and
    latency; deterministic agents remain responsible for non-LLM calculations.
    """

    if attempts < 1:
        raise ValueError("attempts must be positive")

    current_prompt = prompt
    last_response = ""
    last_error = "unknown validation error"
    for attempt in range(attempts):
        last_response = call(current_prompt)
        try:
            return schema.model_validate(extract_json_object(last_response))
        except (ValueError, json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            if attempt + 1 < attempts:
                current_prompt = (
                    f"{prompt}\n\n"
                    "Your previous response did not satisfy the required JSON schema. "
                    "Return the complete corrected JSON object only.\n"
                    f"Validation error: {last_error[:800]}"
                )

    raise StructuredOutputError(
        f"Invalid structured output after {attempts} attempts: {last_error}",
        last_response=last_response,
    )
