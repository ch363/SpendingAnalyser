"""Monthly spend snapshot component."""

from __future__ import annotations

import streamlit as st

from core.models import MonthlySnapshot, SnapshotMetric


def render_monthly_snapshot(snapshot: MonthlySnapshot) -> None:
    """Render the monthly snapshot metrics card."""

    with st.container():
        st.markdown("<div class='snapshot-card'>", unsafe_allow_html=True)

        primary_metric = snapshot.metrics[0] if snapshot.metrics else None
        residual_metrics = snapshot.metrics[1:] if len(snapshot.metrics) > 1 else []

        st.markdown(
            f"""
            <div class="snapshot-card__header">
                <div>
                    <div class="pill">{snapshot.period_label}</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.5rem; font-weight: 600;">{snapshot.title}</h3>
                </div>
                <span class="snapshot-card__badge">Normal for you</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if primary_metric:
            delta_html = ""
            if primary_metric.delta:
                tone = "var(--app-success)" if primary_metric.is_positive else "var(--app-warning)"
                delta_html = (
                    f"<div class='snapshot-card__primary-delta' style='color: {tone};'>{primary_metric.delta}</div>"
                )

            st.markdown(
                f"""
                <div class='snapshot-card__primary'>
                    <div>
                        <div class='snapshot-metric__label'>{primary_metric.label}</div>
                        <div class='snapshot-card__primary-value'>{primary_metric.value}</div>
                    </div>
                    {delta_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

        if residual_metrics:
            st.markdown("<div class='snapshot-grid'>", unsafe_allow_html=True)
            for metric in residual_metrics:
                delta_html = ""
                if metric.delta:
                    tone = "var(--app-success)" if metric.is_positive else "var(--app-warning)"
                    delta_html = (
                        f"<div class='snapshot-metric__delta' style='color: {tone};'>{metric.delta}</div>"
                    )

                st.markdown(
                    f"""
                    <div>
                        <div class='snapshot-metric__label'>{metric.label}</div>
                        <div class='snapshot-metric__value'>{metric.value}</div>
                        {delta_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)


__all__ = ["SnapshotMetric", "MonthlySnapshot", "render_monthly_snapshot"]
