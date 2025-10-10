"""Layout helpers for the Streamlit UI."""

from __future__ import annotations

from datetime import date
from typing import Any

import streamlit as st

import pandas as pd

from app.components import (
    render_ai_summary,
    render_budget_tracker,
    render_category_breakdown,
    render_monthly_snapshot,
    render_subscriptions,
    render_weekly_spend,
    render_recurring_charges,
    render_yearly_net_flow,
)
from analytics.dashboard import DashboardContext, build_dashboard_context

def _coerce_date_range(selection: Any) -> tuple[date, date]:
    if isinstance(selection, (list, tuple)):
        if len(selection) == 0:
            raise ValueError("Date selection must contain at least one date")
        if len(selection) == 1:
            start = end = selection[0]
        else:
            start, end = selection[0], selection[1]
    else:
        start = end = selection

    if start > end:
        start, end = end, start
    return start, end


def _format_range_label(start: date, end: date) -> str:
    if start == end:
        return start.strftime("%b %Y")
    if start.year == end.year:
        return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"
    return f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"


def render_dashboard(
    *,
    default_date_range: tuple[date, date],
    transactions: pd.DataFrame,
) -> None:
    """Compose the two-column dashboard layout."""

    header_left, header_right = st.columns([3, 2], gap="large")

    with header_left:
        st.markdown(
            """
            <div style="margin-bottom: 0.6rem;">
                <h1 style="margin-bottom: 0;">Spending overview</h1>
                <p style="margin-top: 0.35rem; color: var(--app-text-muted);">
                    Preview the upcoming Trading212 spending insights experience.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    min_allowed = min(date(2023, 1, 1), default_date_range[0])
    max_allowed = max(date.today(), default_date_range[1])

    with header_right:
        selection = st.date_input(
            "Select period",
            value=default_date_range,
            min_value=min_allowed,
            max_value=max_allowed,
            key="dashboard_period_selector",
        )

    start_date, end_date = _coerce_date_range(selection)
    range_label = _format_range_label(start_date, end_date)

    header_left.markdown(
        f"<div style='color: var(--app-text-muted); font-weight: 500;'>Viewing: {range_label}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 0.4rem'></div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 1], gap="large")

    context: DashboardContext = build_dashboard_context(
        transactions,
        start_date=start_date,
        end_date=end_date,
    )

    with left_col:
        render_ai_summary(context["ai_summary"])
        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        render_recurring_charges(context["recurring"])

    with right_col:
        with st.container():
            render_monthly_snapshot(context["snapshot"])

        st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

        with st.container():
            render_budget_tracker(context["budget"])

    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)

    render_category_breakdown(context["category_summary"])

    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)

    render_subscriptions(context["subscriptions"])

    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)

    weekly_col, _recurring_col = st.columns([1.4, 1], gap="large")
    with weekly_col:
        render_weekly_spend(context["weekly_spend"])

    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)

    render_yearly_net_flow(context["net_flow"])


__all__ = ["render_dashboard"]
