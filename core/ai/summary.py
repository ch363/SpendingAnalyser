"""AI summarisation utilities for the dashboard hero card."""

from __future__ import annotations

import json
import logging
import os
import re
import inspect
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

try:  # pragma: no cover - OpenAI is optional in some environments
    from openai import OpenAI
except Exception:  # pragma: no cover - library may be missing during tests
    OpenAI = None  # type: ignore

LOGGER = logging.getLogger(__name__)
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class FocusDefinition:
    """Descriptor for an AI focus option supplied to the model."""

    label: str
    guidance: str


SUMMARY_FOCUS_DEFINITIONS: tuple[FocusDefinition, ...] = (
    FocusDefinition(
        label="General",
        guidance=(
            "Summarise overall budget health with a supportive, non-alarmist tone. "
            "Offer specific, bite-sized next steps and include helpful context (e.g., "
            "fixed bills like rent landing at the start of the month can skew week one). "
            "Narrative should be 6-10 sentences."
        ),
    ),
    FocusDefinition(
        label="Categories",
        guidance=(
            "Explain which categories drive spend this month with supportive coaching. "
            "Mention shifts vs prior period and suggest one small, practical optimisation. "
            "Narrative should be 6-10 sentences."
        ),
    ),
    FocusDefinition(
        label="Subscriptions",
        guidance=(
            "Focus on subscription commitments with a calm, constructive tone. Highlight monthly and lifetime cost, "
            "call out notable services, and suggest gentle actions (e.g., pause or downgrade) where it makes sense. "
            "Narrative should be 6-10 sentences."
        ),
    ),
    FocusDefinition(
        label="Recurring",
        guidance=(
            "Cover recurring charges outside subscriptions in a reassuring way. Note upcoming dues, "
            "cash considerations, and one or two simple preparation steps. Narrative should be 6-10 sentences."
        ),
    ),
)


def _ensure_client(api_key: str | None = None) -> Any | None:
    if OpenAI is None:  # dependency not available
        LOGGER.debug("OpenAI client not available")
        return None

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        LOGGER.info("OPENAI_API_KEY not set.")
        return None

    return OpenAI(api_key=key)


def _build_prompt(
    *,
    analytics_context: Mapping[str, Any],
    focus_definitions: Sequence[FocusDefinition],
) -> str:
    payload = {
        "task": (
            "Produce tailored financial coaching snippets for each focus option, "
            "including a 4-7 sentence narrative paragraph and 2-4 bullet tips."
        ),
        "instructions": [
            "Use a calm, supportive, and non-alarmist tone (no fear-trigger words like 'concerning' or 'immediate attention').",
            "Return guidance that is specific, concise, and actionable.",
            "Headlines must be under 110 characters and read like coach messaging.",
            "Paragraph should contain 6-10 sentences.",
            "Provide 3 to 5 supporting bullet points per focus.",
            "Do not hallucinate data. Only use what's provided in analytics_context.",
            "Amounts are in GBP. Preserve the currency when referencing values.",
            "When helpful, include context like fixed bills at the start of the month skewing early-week trends, or payday effects.",
        ],
        "focus_options": [
            {"label": focus.label, "guidance": focus.guidance} for focus in focus_definitions
        ],
        "analytics_context": analytics_context,
        "response_schema": {
            "type": "object",
            "properties": {
                "focus_summaries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "focus": {"type": "string"},
                            "headline": {"type": "string"},
                            "narrative": {"type": "string"},
                            "bullets": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 1,
                                "maxItems": 4,
                            },
                        },
                        "required": ["focus", "headline", "narrative", "bullets"],
                    },
                }
            },
            "required": ["focus_summaries"],
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
                    texts = [str(part.get("text", "")).strip() for part in content if isinstance(part, Mapping)]
                    texts = [text for text in texts if text]
                    if texts:
                        return "\n".join(texts).strip()
    return ""


def _parse_focus_response(payload: str) -> dict[str, dict[str, Any]]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - depends on model quality
        raise ValueError("Invalid JSON returned from OpenAI summary response") from exc

    results: dict[str, dict[str, Any]] = {}
    for entry in data.get("focus_summaries", []):
        focus = entry.get("focus")
        headline = entry.get("headline")
        narrative = entry.get("narrative")
        bullets = entry.get("bullets") or []
        if not focus or not headline:
            continue
        if not isinstance(bullets, Sequence):
            bullets = []
        cleaned_bullets = [str(item) for item in bullets if str(item).strip()]
        results[str(focus)] = {
            "headline": str(headline),
            "narrative": str(narrative) if narrative else "",
            "bullets": cleaned_bullets,
        }
    return results

def build_focus_summaries(
    *,
    analytics_context: Mapping[str, Any],
    focus_definitions: Sequence[FocusDefinition] = SUMMARY_FOCUS_DEFINITIONS,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Generate AI summaries for each focus option."""

    client = _ensure_client(api_key)
    if client is None:
        raise RuntimeError("OpenAI client not configured. Set OPENAI_API_KEY to enable AI summaries.")

    prompt = _build_prompt(
        analytics_context=analytics_context,
        focus_definitions=focus_definitions,
    )

    def _call_with_optional_args(fn: Any, base_kwargs: dict[str, Any], optional_kwargs: dict[str, Any]) -> Any:
        """Call fn with base_kwargs plus optional_kwargs, silently dropping any unsupported kwarg reported by a TypeError.

        This helps with differences between OpenAI SDK versions which may not accept newer optional arguments like
        `response_format` or `max_output_tokens`.
        """
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
                # Look for the typical message when a function doesn't accept a kwarg
                match = re.search(r"unexpected keyword argument '([^']+)'", str(exc))
                if not match:
                    raise
                invalid_key = match.group(1)
                if invalid_key in attempt_kwargs:
                    LOGGER.debug("Dropping unsupported OpenAI parameter: %s", invalid_key)
                    del attempt_kwargs[invalid_key]
                    continue
                raise

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
                "max_output_tokens": 1800,
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
                "max_tokens": 1200,
            }
            optional = {"response_format": {"type": "json_object"}}
            response = _call_with_optional_args(client.chat.completions.create, base, optional)
        else:  # pragma: no cover - should not happen for supported SDKs
            raise RuntimeError("OpenAI client does not support responses or chat.completions APIs")

        payload = _extract_response_payload(response)
        if not payload:
            raise ValueError("Empty response payload from OpenAI summary request")
        parsed = _parse_focus_response(payload)
        if not parsed:
            raise ValueError("OpenAI summary response missing focus content")
        return parsed
    except Exception as exc:  # pragma: no cover - network or API failures
        # Propagate errors so callers can decide how to handle (no heuristics)
        raise RuntimeError(f"OpenAI summary generation failed: {exc}") from exc


__all__ = [
    "DEFAULT_MODEL",
    "FocusDefinition",
    "SUMMARY_FOCUS_DEFINITIONS",
    "build_focus_summaries",
]
