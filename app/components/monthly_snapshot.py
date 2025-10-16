"""Monthly snapshot card built with shared card and metrics utility classes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from html import escape
from textwrap import dedent

import streamlit as st

from core.models import MonthlySnapshot, SnapshotMetric


def _as_snapshot(snapshot: MonthlySnapshot | Mapping[str, object]) -> MonthlySnapshot:
    if isinstance(snapshot, MonthlySnapshot):
        return snapshot
    if not isinstance(snapshot, Mapping):
        raise TypeError("Snapshot must be a MonthlySnapshot or mapping")
    metrics_raw = snapshot.get("metrics", ())
    metrics: list[SnapshotMetric] = []
    if isinstance(metrics_raw, Sequence):
        for item in metrics_raw:
            if isinstance(item, SnapshotMetric):
                metrics.append(item)
            elif isinstance(item, Mapping):
                metrics.append(
                    SnapshotMetric(
                        label=str(item.get("label", "")),
                        value=str(item.get("value", "")),
                        delta=str(item.get("delta")) if item.get("delta") is not None else None,
                        is_positive=item.get("is_positive"),
                    )
                )
    return MonthlySnapshot(
        title=str(snapshot.get("title", "Monthly snapshot")),
        period_label=str(snapshot.get("period_label", "This period")),
        metrics=tuple(metrics),
        baseline_label=str(snapshot.get("baseline_label")) if snapshot.get("baseline_label") is not None else None,
        baseline_tooltip=str(snapshot.get("baseline_tooltip")) if snapshot.get("baseline_tooltip") is not None else None,
    )


def render_snapshot_card(snapshot: MonthlySnapshot | Mapping[str, object]) -> None:
    """Render the monthly snapshot metrics inside a single `.card` container."""

    resolved = _as_snapshot(snapshot)
    metrics = list(resolved.metrics)

    def _delta_html(metric: SnapshotMetric, base_class: str) -> str:
        if not metric.delta:
            return ""
        tone = "pos" if bool(getattr(metric, "is_positive", False)) else "neg"
        return (
            f'<span class="{base_class} {base_class}--{tone}">{escape(str(metric.delta))}</span>'
        )

    primary_metric: SnapshotMetric | None = metrics[0] if metrics else None
    supporting_metrics = metrics[1:] if len(metrics) > 1 else []

    primary_html = ""
    if primary_metric:
        primary_html = dedent(
            f"""\
<div class="snapshot-card__primary">
  <span class="snapshot-card__overline">{escape(primary_metric.label)}</span>
  <div class="snapshot-card__value-row">
    <span class="snapshot-card__value">{escape(primary_metric.value)}</span>
    {_delta_html(primary_metric, "snapshot-card__delta")}
  </div>
</div>
"""
        )

    secondary_blocks: list[str] = []
    for metric in supporting_metrics:
        secondary_blocks.append(
            dedent(
                f"""\
<div class="snapshot-card__metric">
  <span class="snapshot-card__metric-label">{escape(metric.label)}</span>
  <span class="snapshot-card__metric-value">{escape(metric.value)}</span>
  {_delta_html(metric, "snapshot-card__metric-delta")}
</div>
"""
            )
        )
    secondary_html = (
        f"<div class=\"snapshot-card__grid\">{''.join(secondary_blocks)}</div>"
        if secondary_blocks
        else ""
    )

    # Safely handle older MonthlySnapshot instances that may not have the new fields
    baseline_label = getattr(resolved, "baseline_label", None)
    baseline_tooltip = getattr(resolved, "baseline_tooltip", None)

    header_html = dedent(
        f"""\
<header class="snapshot-card__header">
  <div>
    <span class="snapshot-card__period">{escape(resolved.period_label)}</span>
    <h2 class="snapshot-card__title">{escape(resolved.title)}</h2>
  </div>
  <span class="badge snapshot-card__badge" aria-label="Compared to your history" title="{escape(baseline_tooltip or 'Median daily spend over last 90 days, excluding rent & other fixed charges')}">{escape(baseline_label or 'Normal for you')}</span>
</header>
"""
    )

    card_html = dedent(
        f"""\
<section class="card snapshot-card snapshot-card--modern" role="region" aria-label="Monthly snapshot">
  {header_html}
  {primary_html}
  {secondary_html}
</section>
"""
    )
    st.markdown(card_html, unsafe_allow_html=True)


__all__ = ["render_snapshot_card"]
