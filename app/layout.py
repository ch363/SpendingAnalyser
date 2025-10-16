"""Layout helpers for the Streamlit UI."""

from __future__ import annotations

from datetime import date, timedelta
import calendar
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

from app.components import (
    render_ai_summary_card,
    render_budget_tracker,
    render_category_breakdown,
    render_recurring_charges,
    render_snapshot_card,
    render_subscriptions,
    render_weekly_spend,
    render_yearly_net_flow,
)
from analytics.dashboard import DashboardContext, build_dashboard_context
from core.models import AISummary, AISummaryFocus

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


def _month_bounds(d: date) -> tuple[date, date]:
    """Return the first and last day for the month containing ``d``."""
    start = d.replace(day=1)
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    end = d.replace(day=days_in_month)
    return start, end


def _last_month_bounds(today: date) -> tuple[date, date]:
    """Return first/last dates for the previous calendar month relative to ``today``."""
    first_this, _ = _month_bounds(today)
    last_prev = first_this - timedelta(days=1)
    return _month_bounds(last_prev)


def _days_complete_text(start: date, end: date) -> tuple[str, bool, int]:
    """Return human text for days complete and whether it's a partial month.

    Returns: (text, is_partial_month, observed_days)
    """
    if start.year == end.year and start.month == end.month:
        dim = calendar.monthrange(start.year, start.month)[1]
        observed = (end - start).days + 1
        if start.day == 1 and end.day < dim:
            return f"{observed} of {dim} days complete.", True, observed
        if start.day == 1 and end.day == dim:
            return f"{dim} of {dim} days complete.", False, observed
        return f"{observed} days selected.", True, observed
    observed = (end - start).days + 1
    return f"{observed} days selected.", True, observed


def _resolve_focus(
    summary: AISummary,
    key: str,
    fallback: AISummaryFocus,
) -> tuple[str, list[str], dict[str, AISummaryFocus], AISummaryFocus]:
    """Ensure a valid focus is tracked in session state and return helper metadata."""

    focus_map = dict(summary.focus_summaries)
    options = list(summary.focus_options) or list(focus_map.keys())

    default_focus = summary.default_focus if summary.default_focus in focus_map else (options[0] if options else "")

    selected = st.session_state.get(key, default_focus)

    if options:
        if selected not in focus_map:
            selected = default_focus
        if selected:
            st.session_state[key] = selected
    else:
        selected = default_focus or ""
        if key in st.session_state:
            st.session_state.pop(key)

    summary_value = focus_map.get(selected, fallback)
    return selected, options, focus_map, summary_value


def render_dashboard(
    *,
    default_date_range: tuple[date, date],
    transactions: pd.DataFrame,
) -> None:
    """Compose the dashboard layout with shared components and utilities."""

    st.markdown('<main class="app-shell">', unsafe_allow_html=True)

    header_left, header_right = st.columns([3, 2], gap="large")

    with header_left:
        st.markdown(
            dedent(
                """
                <div>
                  <h1 class="section-title">Spending overview</h1>
                  <p class="page-subtitle">Preview the upcoming Trading212 spending insights experience.</p>
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    min_allowed = min(date(2023, 1, 1), default_date_range[0])
    max_allowed = max(date.today(), default_date_range[1])

    with header_right:
        # Period chips
        period_mode = st.segmented_control(
            "Period",
            options=["This month", "Last month", "Custom"],
            key="dashboard_period_mode",
        )

        selection: Any
        if period_mode == "Custom":
            selection = st.date_input(
                "Reporting period",
                value=default_date_range,
                min_value=min_allowed,
                max_value=max_allowed,
                key="dashboard_period_selector",
            )
            st.markdown(
                "<p class='input-helper'>Pick any dates. For monthly clarity, choose the 1st to the last day.</p>",
                unsafe_allow_html=True,
            )
            start_date, end_date = _coerce_date_range(selection)
        elif period_mode == "Last month":
            start_date, end_date = _last_month_bounds(date.today())
            st.markdown(
                "<p class='input-helper'>Showing the complete previous calendar month.</p>",
                unsafe_allow_html=True,
            )
        else:  # This month
            m_start, m_end = _month_bounds(date.today())
            start_date, end_date = m_start, min(m_end, date.today())
            st.markdown(
                "<p class='input-helper'>This month to date.</p>",
                unsafe_allow_html=True,
            )

    range_label = _format_range_label(start_date, end_date)
    days_text, is_partial, observed_days = _days_complete_text(start_date, end_date)

    proj_text = (
        f"<br/>Projections are based on the first {observed_days} days of data."
        if is_partial
        else ""
    )

    st.markdown(
        f"<div class='page-meta'>Viewing: {range_label}<br/>{days_text}{proj_text}</div>",
        unsafe_allow_html=True,
    )

    # Show a simple loading indicator while AI insights (and related forecasts) are generated
    with st.spinner("Generating AI insights…"):
        context: DashboardContext = build_dashboard_context(
            transactions,
            start_date=start_date,
            end_date=end_date,
        )

    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    left_col, right_col = st.columns([2, 1], gap="large")

    with left_col:
        ai_summary: AISummary = context["ai_summary"]
        fallback_focus = AISummaryFocus(
            headline="Spending insights",
            narrative="Connect your accounts to unlock personalised insights.",
            supporting_points=(),
        )

        (
            current_focus,
            focus_options,
            focus_map,
            focus_summary,
        ) = _resolve_focus(ai_summary, "dashboard_ai_focus", fallback_focus)

        if focus_options:
            select_index = focus_options.index(current_focus) if current_focus in focus_options else 0
            selected_focus = st.selectbox(
                "Insight focus",
                options=focus_options,
                index=select_index,
                key="dashboard_ai_focus",
            )
            focus_summary = focus_map.get(selected_focus, fallback_focus)

        render_ai_summary_card(
            focus_summary.headline,
            focus_summary.narrative,
            focus_summary.supporting_points,
        )

        st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
        render_recurring_charges(context["recurring"])

    with right_col:
        render_snapshot_card(context["snapshot"])
        # st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
        render_budget_tracker(context["budget"])

    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    render_category_breakdown(context["category_summary"])

    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    week_col, subs_col = st.columns([1.4, 1], gap="large")
    with week_col:
        render_weekly_spend(context["weekly_spend"])
    with subs_col:
        render_subscriptions(context["subscriptions"])

    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    render_yearly_net_flow(context["net_flow"])

    st.markdown("</main>", unsafe_allow_html=True)


__all__ = ["render_dashboard"]
