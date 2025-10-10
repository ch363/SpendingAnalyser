"""Monthly spend snapshot component."""

from __future__ import annotations

from textwrap import dedent

import streamlit as st

from core.models import MonthlySnapshot, SnapshotMetric


def render_monthly_snapshot(snapshot: MonthlySnapshot) -> None:
    """Render the monthly snapshot metrics card."""

    with st.container():
        primary_metric = snapshot.metrics[0] if snapshot.metrics else None
        residual_metrics = snapshot.metrics[1:] if len(snapshot.metrics) > 1 else []

        header_html = dedent(
            f"""
            <div class="snapshot-card__header">
                <div>
                    <div class="pill">{snapshot.period_label}</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.5rem; font-weight: 600;">{snapshot.title}</h3>
                </div>
                <span class="snapshot-card__badge">Normal for you</span>
            </div>
            """
        ).strip()

        if primary_metric:
            if primary_metric.delta:
                tone = "var(--app-success)" if primary_metric.is_positive else "var(--app-warning)"
                delta_html = (
                    f"<div class='snapshot-card__primary-delta' style='color: {tone};'>{primary_metric.delta}</div>"
                )
            else:
                delta_html = ""

            primary_html = dedent(
                f"""
                <div class='snapshot-card__primary'>
                    <div>
                        <div class='snapshot-metric__label'>{primary_metric.label}</div>
                        <div class='snapshot-card__primary-value'>{primary_metric.value}</div>
                    </div>
                    {delta_html}
                </div>
                """
            ).strip()
        else:
            primary_html = ""

        residual_blocks: list[str] = []
        for metric in residual_metrics:
            if metric.delta:
                tone = "var(--app-success)" if metric.is_positive else "var(--app-warning)"
                delta_html = f"<div class='snapshot-metric__delta' style='color: {tone};'>{metric.delta}</div>"
            else:
                delta_html = ""
            residual_blocks.append(
                dedent(
                    f"""
                    <div>
                        <div class='snapshot-metric__label'>{metric.label}</div>
                        <div class='snapshot-metric__value'>{metric.value}</div>
                        {delta_html}
                    </div>
                    """
                ).strip()
            )

        residual_html = (
            f"<div class='snapshot-grid'>{''.join(residual_blocks)}</div>" if residual_blocks else ""
        )

        card_html = dedent(
            f"""
            <div class='snapshot-card'>
                {header_html}
                {primary_html}
                {residual_html}
            </div>
            """
        ).strip()

        st.markdown(card_html, unsafe_allow_html=True)


__all__ = ["SnapshotMetric", "MonthlySnapshot", "render_monthly_snapshot"]
