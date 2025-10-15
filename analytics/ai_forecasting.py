"""OpenAI-powered forecasting helpers for weekly spend projections."""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

try:  # pragma: no cover - optional dependency at runtime
    from openai import OpenAI
except Exception:  # pragma: no cover - library may be missing in some environments
    OpenAI = None  # type: ignore

LOGGER = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class WeeklyHistoryRecord:
    """Summary of a historic spend week."""

    week_of_month: int
    month: str
    year: int
    start_date: str
    end_date: str
    amount: float
    notes: str | None = None


@dataclass(frozen=True)
class WeeklyForecastRequest:
    """Descriptor for a future week that requires a forecast."""

    week_of_month: int
    start_date: str
    end_date: str
    recurring_commitments: float


@dataclass(frozen=True)
class WeeklyForecastResult:
    """Structured forecast result returned by an AI model or heuristic."""

    week_of_month: int
    amount: float
    confidence: float


def _ensure_client(api_key: str | None = None) -> Any | None:
    if OpenAI is None:  # dependency not available
        LOGGER.debug("OpenAI client not available; falling back to heuristics")
        return None

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        LOGGER.info("OPENAI_API_KEY not set. Falling back to heuristic forecast.")
        return None

    return OpenAI(api_key=key)


def _build_prompt(
    history: Sequence[WeeklyHistoryRecord],
    actuals: Sequence[WeeklyHistoryRecord],
    upcoming: Sequence[WeeklyForecastRequest],
) -> str:
    history_payload = [record.__dict__ for record in history]
    actual_payload = [record.__dict__ for record in actuals]
    upcoming_payload = [record.__dict__ for record in upcoming]

    instructions = {
        "task": "Forecast weekly spend totals for the remainder of the selected month.",
        "guidelines": [
            "Factor in recurring commitments noted in each future week.",
            "Earlier weeks in a month often show higher spend due to rent and utilities.",
            "Use the historical records to understand typical spend patterns per week of month.",
            "Respond with JSON containing forecasts ordered by week_of_month.",
            "Provide a confidence score between 0 and 1 for each forecast.",
            "Keep results in the currency scale of the inputs (GBP).",
        ],
        "history": history_payload,
        "observed_weeks": actual_payload,
        "upcoming_weeks": upcoming_payload,
        "response_schema": {
            "type": "object",
            "properties": {
                "forecasts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "week_of_month": {"type": "integer"},
                            "amount": {"type": "number"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["week_of_month", "amount"],
                    },
                }
            },
            "required": ["forecasts"],
        },
    }

    return json.dumps(instructions)


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


def _extract_json_segment(text: str) -> str | None:
    stack: list[str] = []
    start_idx: int | None = None
    for idx, char in enumerate(text):
        if char in "{[":
            if not stack:
                start_idx = idx
            stack.append(char)
        elif char in "]}":
            if not stack:
                continue
            opener = stack.pop()
            if (opener == "{" and char != "}") or (opener == "[" and char != "]"):
                stack.clear()
                start_idx = None
                continue
            if not stack and start_idx is not None:
                segment = text[start_idx : idx + 1]
                try:
                    json.loads(segment)
                    return segment
                except json.JSONDecodeError:
                    start_idx = None
    return None


def _normalise_json_payload(payload: str) -> str:
    cleaned = payload.strip()
    if not cleaned:
        return ""

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    segment = _extract_json_segment(cleaned)
    if segment:
        return segment

    try:
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and start < end:
        candidate = cleaned[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    return cleaned


def _parse_forecast_response(payload: str) -> list[WeeklyForecastResult]:
    payload = _normalise_json_payload(payload)
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:  # pragma: no cover - depends on model response
        raise ValueError("Invalid JSON returned from OpenAI") from exc

    forecasts = []
    for item in data.get("forecasts", []):
        try:
            week = int(item["week_of_month"])
            amount = float(item["amount"])
            confidence = float(item.get("confidence", 0.6))
        except (KeyError, TypeError, ValueError):
            continue
        forecasts.append(WeeklyForecastResult(week, amount, max(0.0, min(confidence, 1.0))))
    return forecasts


def _heuristic_forecast(
    history: Sequence[WeeklyHistoryRecord],
    actuals: Sequence[WeeklyHistoryRecord],
    upcoming: Sequence[WeeklyForecastRequest],
) -> list[WeeklyForecastResult]:
    """Fallback forecast using simple statistical heuristics."""

    if not upcoming:
        return []

    by_week: dict[int, list[float]] = {}
    for record in history:
        by_week.setdefault(record.week_of_month, []).append(record.amount)

    history_means = {week: float(np.mean(values)) for week, values in by_week.items() if values}
    default_mean = float(np.mean([record.amount for record in history])) if history else 0.0

    results: list[WeeklyForecastResult] = []
    for future in upcoming:
        base = history_means.get(future.week_of_month, default_mean)
        amount = base + future.recurring_commitments
        confidence = 0.35 if base == 0 else 0.55
        results.append(WeeklyForecastResult(future.week_of_month, amount, confidence))
    return results


def forecast_weekly_spend(
    *,
    history: Sequence[WeeklyHistoryRecord],
    actuals: Sequence[WeeklyHistoryRecord],
    upcoming: Sequence[WeeklyForecastRequest],
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> list[WeeklyForecastResult]:
    """Generate AI-assisted weekly spend forecasts.

    Falls back to a heuristic approach if the OpenAI client is unavailable.
    """

    client = _ensure_client(api_key)
    if client is None:
        return _heuristic_forecast(history, actuals, upcoming)

    prompt = _build_prompt(history, actuals, upcoming)

    try:
        try:
            response = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": "You are a financial forecasting assistant."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
        except TypeError as exc:
            # Some SDK versions don't accept `response_format` — retry without it
            if "response_format" in str(exc):
                response = client.responses.create(
                    model=model,
                    input=[
                        {"role": "system", "content": "You are a financial forecasting assistant."},
                        {"role": "user", "content": prompt},
                    ],
                )
            else:
                raise
        payload = _extract_response_payload(response)
        if not payload:
            raise ValueError("No output from OpenAI response")
        return _parse_forecast_response(payload)
    except Exception as exc:  # pragma: no cover - network or API failures
        LOGGER.warning("OpenAI forecast failed, using heuristic fallback: %s", exc)
        return _heuristic_forecast(history, actuals, upcoming)


__all__ = [
    "WeeklyHistoryRecord",
    "WeeklyForecastRequest",
    "WeeklyForecastResult",
    "forecast_weekly_spend",
]
