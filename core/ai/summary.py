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
            "Summarise overall budget health, key swings, and a forward-looking "
            "coaching action. Narrative should be 4-7 sentences."
        ),
    ),
    FocusDefinition(
        label="Categories",
        guidance=(
            "Explain which categories drive spend this month, mention shifts versus "
            "prior period, and include an optimisation idea. Narrative should be 4-7 sentences."
        ),
    ),
    FocusDefinition(
        label="Subscriptions",
        guidance=(
            "Focus on subscription commitments, highlight monthly and lifetime cost, "
            "call out notable services, and advise on cancellations or downgrades. Narrative should be 4-7 sentences."
        ),
    ),
    FocusDefinition(
        label="Recurring",
        guidance=(
            "Cover recurring charges outside subscriptions, noting upcoming dues, "
            "cash considerations, and preparation steps. Narrative should be 4-7 sentences."
        ),
    ),
)


def _ensure_client(api_key: str | None = None) -> Any | None:
    if OpenAI is None:  # dependency not available
        LOGGER.debug("OpenAI client not available; using heuristic summaries")
        return None

    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        LOGGER.info("OPENAI_API_KEY not set. Falling back to heuristic summaries.")
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
            "Return guidance that is specific, concise, and actionable.",
            "Headlines must be under 110 characters and read like coach messaging.",
            "Paragraph should contain 4-7 sentences.",
            "Provide 2 to 4 supporting bullet points per focus.",
            "Do not hallucinate data. Only use what's provided in analytics_context.",
            "Amounts are in GBP. Preserve the currency when referencing values.",
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


def _format_currency(value: float) -> str:
    return f"£{value:,.0f}"


def _month_label(analytics_context: Mapping[str, Any]) -> str:
    timeframe = analytics_context.get("timeframe", {})
    start_date = timeframe.get("start_date")
    end_date = timeframe.get("end_date")
    period_label = analytics_context.get("snapshot", {}).get("period_label")

    def _format(value: str | None) -> str | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).strftime("%B %Y")
        except Exception:  # pragma: no cover - depends on data quality
            return None

    start_label = _format(start_date)
    end_label = _format(end_date)
    if start_label and end_label and start_label == end_label:
        return start_label
    if start_label and end_label:
        return f"{start_label} to {end_label}"
    return period_label or start_label or end_label or "this month"


def _ensure_narrative(sentences: list[str], *, fallback: str) -> str:
    cleaned = [" ".join(sentence.strip().split()) for sentence in sentences if sentence and sentence.strip()]
    if not cleaned:
        cleaned = [fallback]
    while len(cleaned) < 4:
        cleaned.append(fallback)
    return " ".join(cleaned[:7])


def _heuristic_summaries(
    *,
    analytics_context: Mapping[str, Any],
    focus_definitions: Sequence[FocusDefinition],
) -> dict[str, dict[str, Any]]:
    budget = analytics_context.get("budget", {})
    categories = analytics_context.get("categories", [])
    snapshot_metrics = analytics_context.get("snapshot_metrics", [])
    subscriptions = analytics_context.get("subscriptions", {})
    recurring = analytics_context.get("recurring", {})

    headline_direction = "under" if budget.get("is_under_budget") else "over"
    gap = abs(float(budget.get("savings_projection", 0.0)))
    projected = float(budget.get("projected_or_actual_spend", 0.0))
    variance_pct = float(budget.get("variance_percent", 0.0)) * 100

    month_name = _month_label(analytics_context)

    general_points: list[str] = []
    if snapshot_metrics:
        primary = snapshot_metrics[0]
        label = primary.get("label", "Key metric")
        value = primary.get("value", "n/a")
        delta = primary.get("delta") or "no change vs prior period"
        general_points.append(f"{label}: {value} ({delta})")
    if variance_pct:
        direction_word = "below" if variance_pct < 0 else "above"
        general_points.append(f"Spend is {abs(variance_pct):.1f}% {direction_word} plan so far.")
    if categories:
        top = categories[0]
        general_points.append(
            f"{top.get('name', 'Top category')} leading at {_format_currency(float(top.get('amount', 0)))}."
        )

    general_sentences: list[str] = [
        f"In {month_name}, spend is tracking {headline_direction} budget by {_format_currency(gap)}.",
        f"Projected month-end outlay is {_format_currency(projected)} against a plan of {_format_currency(float(budget.get('allocated_budget', projected)))}.",
    ]
    if snapshot_metrics:
        primary = snapshot_metrics[0]
        general_sentences.append(
            f"Key indicator {primary.get('label', 'primary metric')} is at {primary.get('value', 'n/a')} ({primary.get('delta') or 'no change'})."
        )
    if categories:
        general_sentences.append(
            f"{categories[0].get('name', 'Leading category')} continues to drive spend with {_format_currency(float(categories[0].get('amount', 0.0)))} this period."
        )
    if savings := gap:
        general_sentences.append(
            f"Savings projection currently stands at {_format_currency(savings)}."
        )
    general_sentences.append("Stay proactive by reviewing upcoming commitments and nudging high-growth categories back in line.")

    fallback_results: dict[str, dict[str, Any]] = {
        "General": {
            "headline": (
                f"Tracking {headline_direction} budget by {_format_currency(gap)} with "
                f"an outlook of {_format_currency(projected)}."
            ),
            "narrative": _ensure_narrative(
                general_sentences,
                fallback="Keep watch on cash flow to stay ahead of plan.",
            ),
            "bullets": general_points or ["Keep monitoring categories to stay ahead of plan."],
        }
    }

    if categories:
        top = categories[0]
        second = categories[1] if len(categories) > 1 else None
        merchants = top.get("merchants", [])
        points = [
            f"Accounts for {float(top.get('share', 0.0)) * 100:.1f}% of spend",
        ]
        if merchants:
            points.append(
                f"{merchants[0].get('name', 'Top merchant')} totals {_format_currency(float(merchants[0].get('amount', 0.0)))}"
            )
        if second:
            points.append(
                f"Next category: {second.get('name', 'Next up')} at {_format_currency(float(second.get('amount', 0.0)))}"
            )
        category_sentences = [
            f"In {month_name}, {top.get('name', 'top category')} leads spending at {_format_currency(float(top.get('amount', 0.0)))}.",
            f"It represents {float(top.get('share', 0.0)) * 100:.1f}% of the month's outgoings.",
        ]
        if merchants:
            category_sentences.append(
                f"{merchants[0].get('name', 'Top merchant')} is the biggest contributor with {_format_currency(float(merchants[0].get('amount', 0.0)))} spent."
            )
        if second:
            category_sentences.append(
                f"Next up is {second.get('name', 'next category')} at {_format_currency(float(second.get('amount', 0.0)))}."
            )
        category_sentences.append("Reallocate a portion of discretionary spend to protect priority goals.")

        fallback_results["Categories"] = {
            "headline": f"{top.get('name', 'Top category')} is the biggest driver",
            "narrative": _ensure_narrative(
                category_sentences,
                fallback="Focus spending on the categories that advance your goals.",
            ),
            "bullets": points,
        }
    else:
        fallback_results["Categories"] = {
            "headline": "Spending categories are evenly balanced",
            "narrative": _ensure_narrative(
                [f"Spending patterns in {month_name} are broadly even with no dominant categories."],
                fallback="Monitor transactions to surface category-led opportunities.",
            ),
            "bullets": ["No dominant categories detected this period."],
        }

    subscription_items = subscriptions.get("items", [])
    if subscription_items:
        top_sub = subscription_items[0]
        total_monthly = float(subscriptions.get("total_monthly", 0.0))
        total_cumulative = float(subscriptions.get("total_cumulative", 0.0))
        subscription_sentences = [
            f"Subscriptions total {_format_currency(total_monthly)} each month in {month_name}.",
            f"Lifetime spend has reached {_format_currency(total_cumulative)} across {len(subscription_items)} services.",
            f"{top_sub.get('name', 'Leading service')} remains the highest commitment at {_format_currency(float(top_sub.get('monthly_cost', 0.0)))} per month.",
            "Review whether usage still justifies each cost and downgrade where it doesn't.",
        ]
        fallback_results["Subscriptions"] = {
            "headline": f"{top_sub.get('name', 'Subscription')} tops monthly commitments",
            "narrative": _ensure_narrative(
                subscription_sentences,
                fallback="Audit subscriptions to ensure each one earns its place in the budget.",
            ),
            "bullets": [
                f"Monthly total {_format_currency(total_monthly)} across {len(subscription_items)} services",
                f"Lifetime cost {_format_currency(total_cumulative)}",
                f"{top_sub.get('name', 'Top subscription')} costs {_format_currency(float(top_sub.get('monthly_cost', 0.0)))} per month",
            ],
        }
    else:
        fallback_results["Subscriptions"] = {
            "headline": "No active subscriptions in the selected period",
            "narrative": _ensure_narrative(
                [f"No subscription activity surfaced for {month_name}, keeping fixed commitments light."],
                fallback="Healthy subscription hygiene keeps cash free for priorities.",
            ),
            "bullets": ["Add subscription transactions to unlock insights."],
        }

    recurring_items = recurring.get("items", [])
    if recurring_items:
        next_due = recurring_items[0]
        recurring_sentences = [
            f"Recurring commitments outside subscriptions remain a watchpoint in {month_name}.",
            f"Next up is {next_due.get('name', 'a recurring charge')} on {next_due.get('next_date', 'n/a')} for {_format_currency(float(next_due.get('amount', 0.0)))}.",
            "Confirm cash is set aside before the charge lands.",
            "Log any new agreements quickly so surprises are avoided.",
        ]
        fallback_results["Recurring"] = {
            "headline": f"{next_due.get('name', 'Recurring charge')} coming up",
            "narrative": _ensure_narrative(
                recurring_sentences,
                fallback="Staying ahead of recurring outgoings protects monthly cash flow.",
            ),
            "bullets": [
                f"Next due on {next_due.get('next_date', 'n/a')} ({next_due.get('cadence', 'cadence unknown')})",
                f"Amount {_format_currency(float(next_due.get('amount', 0.0)))}",
                "Ensure funds allocated before due date.",
            ],
        }
    else:
        fallback_results["Recurring"] = {
            "headline": "No recurring commitments detected",
            "narrative": _ensure_narrative(
                [f"There are no recurring commitments flagged for {month_name}, freeing up short-term liquidity."],
                fallback="Track upcoming bills to avoid last-minute scrambles.",
            ),
            "bullets": ["Monitor upcoming bills to avoid surprises."],
        }

    # Ensure every focus option has coverage even if heuristics above missed it.
    for focus in focus_definitions:
        fallback_results.setdefault(
            focus.label,
            {
                "headline": "No insights available",
                "narrative": _ensure_narrative(
                    ["Not enough data to generate guidance just yet."],
                    fallback="Collect more transaction history to unlock tailored advice.",
                ),
                "bullets": ["Not enough data to generate guidance."],
            },
        )

    return fallback_results


def build_focus_summaries(
    *,
    analytics_context: Mapping[str, Any],
    focus_definitions: Sequence[FocusDefinition] = SUMMARY_FOCUS_DEFINITIONS,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Generate AI or heuristic summaries for each focus option."""

    client = _ensure_client(api_key)
    if client is None:
        return _heuristic_summaries(
            analytics_context=analytics_context,
            focus_definitions=focus_definitions,
        )

    prompt = _build_prompt(
        analytics_context=analytics_context,
        focus_definitions=focus_definitions,
    )

    def _call_with_optional_args(
        fn: Any,
        base_kwargs: dict[str, Any],
        optional_kwargs: dict[str, Any],
    ) -> Any:
        attempt_kwargs = dict(base_kwargs)
        try:
            signature = inspect.signature(fn)
            params = signature.parameters
        except (TypeError, ValueError):
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
                match = re.search(r"got an unexpected keyword argument '([^']+)'", str(exc))
                if not match:
                    raise
                invalid_key = match.group(1)
                if invalid_key not in attempt_kwargs:
                    raise
                LOGGER.debug("Removing unsupported OpenAI parameter: %s", invalid_key)
                del attempt_kwargs[invalid_key]

    try:
        response = None
        if hasattr(client, "responses"):
            responses_base = dict(
                model=model,
                input=[
                    {"role": "system", "content": "You are a concise financial coach."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_output_tokens=1200,
            )
            response = _call_with_optional_args(
                client.responses.create,
                responses_base,
                {"response_format": {"type": "json_object"}},
            )
        elif hasattr(client, "chat") and hasattr(client.chat, "completions"):
            chat_base = dict(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a concise financial coach."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=800,
            )
            response = _call_with_optional_args(
                client.chat.completions.create,
                chat_base,
                {"response_format": {"type": "json_object"}},
            )
        else:  # pragma: no cover - should not happen for supported SDKs
            raise RuntimeError("OpenAI client does not support responses or chat.completions APIs")

        payload = _extract_response_payload(response)
        if not payload:
            raise ValueError("Empty response payload from OpenAI summary request")
        parsed = _parse_focus_response(payload)
        if not parsed:
            raise ValueError("OpenAI summary response missing focus content")
        # Fill any missing focus entries with heuristics
        fallback = _heuristic_summaries(
            analytics_context=analytics_context,
            focus_definitions=focus_definitions,
        )
        general_fallback = fallback.get("General") or next(iter(fallback.values()))
        for focus in focus_definitions:
            existing = parsed.get(focus.label)
            fallback_entry = fallback.get(focus.label, general_fallback)
            if not existing:
                parsed[focus.label] = fallback_entry
                continue
            # Backfill missing fields from heuristic data
            if not existing.get("narrative") and fallback_entry.get("narrative"):
                existing["narrative"] = fallback_entry["narrative"]
            if not existing.get("bullets") and fallback_entry.get("bullets"):
                existing["bullets"] = fallback_entry["bullets"]
            if not existing.get("headline") and fallback_entry.get("headline"):
                existing["headline"] = fallback_entry["headline"]
        return parsed
    except Exception as exc:  # pragma: no cover - network or API failures
        LOGGER.warning("OpenAI summary generation failed, using heuristic fallback: %s", exc)
        return _heuristic_summaries(
            analytics_context=analytics_context,
            focus_definitions=focus_definitions,
        )


__all__ = [
    "DEFAULT_MODEL",
    "FocusDefinition",
    "SUMMARY_FOCUS_DEFINITIONS",
    "build_focus_summaries",
]
