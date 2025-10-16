"""AI-powered budget target suggestions.

This module provides a tiny wrapper around the OpenAI client to generate
monthly budget target suggestions based on the user's current month stats.

Pure AI, no heuristics: if the OpenAI client isn't available, callers should
catch the RuntimeError and decide how to handle (e.g., show a muted message).
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

try:  # pragma: no cover - OpenAI is optional in some environments
    from openai import OpenAI
except Exception:  # pragma: no cover - library may be missing during tests
    OpenAI = None  # type: ignore

LOGGER = logging.getLogger(__name__)
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class BudgetSuggestion:
    label: str
    amount: float
    rationale: str


def _ensure_client(api_key: str | None = None) -> Any | None:
    if OpenAI is None:  # dependency not available
        LOGGER.debug("OpenAI client not available")
        return None

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        LOGGER.info("OPENAI_API_KEY not set.")
        return None

    return OpenAI(api_key=key)


def _build_prompt(*, analytics_context: Mapping[str, Any]) -> str:
    """Construct a strict-JSON prompt describing the budget decision.

    The model is asked to return 1 primary suggestion and up to 2 alternatives
    with short rationales. All amounts must be in GBP and integers for display
    clarity. Keep the rationale concise (≤ 20 words) and supportive.
    """
    payload = {
        "task": "Recommend a monthly budget target based on current month stats.",
        "instructions": [
            "Return concise, supportive guidance. No alarmist language.",
            "Amounts are GBP and should be whole numbers (round to the nearest £).",
            "Provide one primary suggestion and up to two alternatives.",
            "Each suggestion must include: label, amount, and a ≤20-word rationale.",
            "Do not hallucinate data beyond analytics_context.",
        ],
        "analytics_context": analytics_context,
        "response_schema": {
            "type": "object",
            "properties": {
                "primary": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "amount": {"type": "number"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["label", "amount", "rationale"],
                },
                "alternatives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "amount": {"type": "number"},
                            "rationale": {"type": "string"},
                        },
                        "required": ["label", "amount", "rationale"],
                    },
                },
            },
            "required": ["primary"],
        },
    }
    return json.dumps(payload)


def _extract_response_payload(response: Any) -> str:
    if response is None:
        return ""

    if hasattr(response, "output_text") and getattr(response, "output_text"):
        return str(getattr(response, "output_text")).strip()

    text_chunks: list[str] = []

    output = getattr(response, "output", None)
    if output:
        for item in output:
            contents = getattr(item, "content", [])
            for content in contents:
                if getattr(content, "type", None) == "text":
                    text = getattr(content, "text", None)
                    if text:
                        text_chunks.append(str(text))
    if text_chunks:
        return "\n".join(text_chunks).strip()

    choices = getattr(response, "choices", None)
    if choices:
        first = choices[0] if choices else None
        if first is not None:
            message = getattr(first, "message", None)
            if message is not None:
                content = getattr(message, "content", None)
                if isinstance(content, str):
                    return content.strip()
                if isinstance(content, list):
                    texts = [str(part.get("text", "")).strip() for part in content if isinstance(part, dict)]
                    texts = [text for text in texts if text]
                    if texts:
                        return "\n".join(texts).strip()
    return ""


def _parse_response(payload: str) -> tuple[BudgetSuggestion, list[BudgetSuggestion]]:
    data = json.loads(payload)
    p = data.get("primary") or {}
    primary = BudgetSuggestion(
        label=str(p.get("label", "Suggested")),
        amount=float(p.get("amount", 0.0)),
        rationale=str(p.get("rationale", "")),
    )
    alts: list[BudgetSuggestion] = []
    for item in data.get("alternatives", []) or []:
        try:
            alts.append(
                BudgetSuggestion(
                    label=str(item.get("label", "")),
                    amount=float(item.get("amount", 0.0)),
                    rationale=str(item.get("rationale", "")),
                )
            )
        except Exception:
            continue
    return primary, alts


def _call_with_optional_args(fn: Any, base_kwargs: dict[str, Any], optional_kwargs: dict[str, Any]) -> Any:
    """Invoke fn with optional kwargs only if supported by the SDK version."""
    attempt_kwargs = dict(base_kwargs)
    try:
        signature = inspect.signature(fn)
        params = signature.parameters
    except Exception:
        params = None

    if params is None:
        attempt_kwargs.update(optional_kwargs)
    else:
        for key, value in optional_kwargs.items():
            if key in params:
                attempt_kwargs[key] = value

    while True:
        try:
            return fn(**attempt_kwargs)
        except TypeError as exc:
            match = re.search(r"unexpected keyword argument '([^']+)'", str(exc))
            if not match:
                raise
            invalid_key = match.group(1)
            if invalid_key in attempt_kwargs:
                del attempt_kwargs[invalid_key]
                continue
            raise


def generate_budget_suggestions(
    *,
    analytics_context: Mapping[str, Any],
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> tuple[BudgetSuggestion, list[BudgetSuggestion]]:
    """Generate AI budget target suggestions.

    Returns (primary, alternatives). Raises RuntimeError if the OpenAI client is
    not configured or the request fails. Callers can catch and handle.
    """
    client = _ensure_client(api_key)
    if client is None:
        raise RuntimeError("OpenAI client not configured. Set OPENAI_API_KEY to enable AI suggestions.")

    prompt = _build_prompt(analytics_context=analytics_context)

    try:
        response = None
        if hasattr(client, "responses"):
            base = {
                "model": model,
                "input": [
                    {"role": "system", "content": "You are a concise financial coach."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_output_tokens": 600,
            }
            optional = {"response_format": {"type": "json_object"}}
            response = _call_with_optional_args(client.responses.create, base, optional)
        elif hasattr(client, "chat") and hasattr(client.chat, "completions"):
            base = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a concise financial coach."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 500,
            }
            optional = {"response_format": {"type": "json_object"}}
            response = _call_with_optional_args(client.chat.completions.create, base, optional)
        else:  # pragma: no cover - unsupported SDK
            raise RuntimeError("OpenAI client does not support responses or chat.completions APIs")

        payload = _extract_response_payload(response)
        if not payload:
            raise ValueError("Empty response payload from OpenAI suggestion request")
        return _parse_response(payload)
    except Exception as exc:  # pragma: no cover - network or API failures
        raise RuntimeError(f"OpenAI budget suggestion failed: {exc}") from exc


__all__ = [
    "BudgetSuggestion",
    "DEFAULT_MODEL",
    "generate_budget_suggestions",
]
