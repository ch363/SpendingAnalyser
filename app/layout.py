"""Layout helpers for the Streamlit UI."""

from __future__ import annotations

from datetime import date, timedelta
import calendar
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from app.components import (
    render_ai_summary_card,
    render_budget_spend_insights,
    render_category_breakdown,
    render_recurring_charges,
    render_snapshot_card,
    render_subscriptions,
    render_weekly_spend,
    render_yearly_net_flow,
)
from analytics.dashboard import build_dashboard_context, build_dashboard_baseline, build_weekly_spend_series
from core.models import AISummary, AISummaryFocus
from core.ai.budget import generate_budget_suggestions, BudgetSuggestion


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

    # Prefer existing widget state if present; otherwise use the computed default.
    # Do not mutate st.session_state here to avoid conflicts with widget defaults.
    selected = st.session_state.get(key, default_focus)

    if options and selected not in focus_map:
        selected = default_focus

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
        # Place label + control into a right-side nested column so the control sits to the right
        _spacer, right_side = st.columns([1, 1])
        with right_side:
            period_mode = st.segmented_control(
                "Period",
                options=["This month", "Last month", "Custom"],
                key="dashboard_period_mode",
            )

        selection: Any
        if period_mode == "Custom":
            with right_side:
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
            with right_side:
                st.markdown(
                    "<p class='input-helper'>Showing the complete previous calendar month.</p>",
                    unsafe_allow_html=True,
                )
        else:  # This month
            m_start, m_end = _month_bounds(date.today())
            start_date, end_date = m_start, min(m_end, date.today())
            with right_side:
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

    # Build baseline sync data immediately so the majority of the page can render.
    baseline = build_dashboard_baseline(
        transactions,
        start_date=start_date,
        end_date=end_date,
    )

    ai_placeholder: DeltaGenerator | None = None
    budget_placeholder: DeltaGenerator | None = None
    baseline_weekly = build_weekly_spend_series(
        baseline["frame"],
        start_date=start_date,
        end_date=end_date,
    )

    def _render_ai_summary(summary: AISummary | None) -> None:
        nonlocal ai_placeholder
        if ai_placeholder is None:
            return

        if summary is None:
            ai_placeholder.empty()
            ai_placeholder.markdown(
                """
                <section class="hero" role="region" aria-label="AI spending summary">
                  <div class="hero__content">
                    <span class="pill">AI summary</span>
                    <h2 class="hero__heading">Generating insights…</h2>
                    <p class="hero__body">We’re analysing your latest transactions.</p>
                    <ul class="hero__actions"><li>Hang tight while the AI spins up.</li></ul>
                  </div>
                </section>
                """,
                unsafe_allow_html=True,
            )
            return

        ai_placeholder.empty()
        with ai_placeholder.container():
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
            ) = _resolve_focus(summary, "dashboard_ai_focus", fallback_focus)

            if focus_options:
                selected_focus = st.segmented_control(
                    "Insight focus",
                    options=focus_options,
                    default=current_focus if current_focus in focus_options else None,
                    key="dashboard_ai_focus",
                )
                selected_value = (
                    selected_focus if isinstance(selected_focus, str) and selected_focus else current_focus
                )
                if not selected_value and focus_options:
                    selected_value = focus_options[0]
                focus_summary = focus_map.get(selected_value, fallback_focus)

            render_ai_summary_card(
                focus_summary.headline,
                focus_summary.narrative,
                focus_summary.supporting_points,
            )

    def _render_budget_insights(budget_tracker: object) -> None:
        nonlocal budget_placeholder
        if budget_placeholder is None:
            return

        budget_placeholder.empty()
        with budget_placeholder.container():
            render_budget_spend_insights(budget_tracker)  # type: ignore[arg-type]

    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    # Compute helper values for budget/AI context using baseline data
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    day_of_month = today.day
    baseline_budget = baseline["budget"]
    budget_value = float(st.session_state.get("monthly_budget_value", baseline_budget.allocated_budget))
    current_spend = float(baseline_budget.current_spend)
    remaining = max(0.0, budget_value - current_spend)
    days_left = max(1, days_in_month - day_of_month)
    daily_allowance = remaining / days_left
    avg_so_far = current_spend / max(1, day_of_month)
    target_pace = budget_value / max(1, days_in_month)
    on_track = avg_so_far <= target_pace
    month_complete = bool(getattr(baseline_budget, "is_month_complete", False))

    def _render_budget_target_card() -> None:
        """Render the target budget input with AI suggestion inside a single card."""
        with st.container():
            # Scope marker so only this container is styled as a card via CSS
            st.markdown("<div class='budget-target-scope'></div>", unsafe_allow_html=True)
            budget_key = "monthly_budget_value"
            pending_key = "pending_budget_value"
            if pending_key in st.session_state:
                try:
                    st.session_state[budget_key] = float(st.session_state.pop(pending_key))
                except Exception:
                    st.session_state.pop(pending_key, None)
            if budget_key not in st.session_state:
                st.session_state[budget_key] = float(budget_value)
            st.number_input(
                "Budget target (£/month)",
                min_value=0.0,
                step=50.0,
                format="%.0f",
                key=budget_key,
                help="What‑if target used for progress, pace, and savings/overspend calculations.",
            )

            suggestion_primary: BudgetSuggestion | None = None
            try:
                analytics_context = {
                    "current_spend": round(current_spend, 2),
                    "target_budget": round(float(st.session_state.get(budget_key, budget_value)), 2),
                    "days_in_month": days_in_month,
                    "day_of_month": day_of_month,
                    "days_remaining": days_left,
                    "remaining_budget": round(remaining, 2),
                    "daily_allowance": round(daily_allowance, 2),
                    "avg_daily_spend_to_date": round(avg_so_far, 2),
                    "target_daily_pace": round(target_pace, 2),
                    "projected_or_actual_spend": round(float(baseline_budget.projected_or_actual_spend), 2),
                    "is_on_track": on_track,
                    "is_month_complete": month_complete,
                }
                primary, _ = generate_budget_suggestions(analytics_context=analytics_context)
                suggestion_primary = BudgetSuggestion(primary.label, float(primary.amount), primary.rationale)
            except Exception:
                suggestion_primary = None

            if suggestion_primary is not None:
                st.markdown(
                    f"<p class='toolbar__helper' style='margin:0;'>AI suggestion: <strong>£{suggestion_primary.amount:,.0f}</strong> — {suggestion_primary.rationale}</p>",
                    unsafe_allow_html=True,
                )
                st.write("")
                if st.button(
                    f"Use {suggestion_primary.label} (£{suggestion_primary.amount:,.0f})",
                    key="apply_ai_budget_suggestion",
                    help="Apply the AI-recommended budget target",
                ):
                    st.session_state[pending_key] = float(suggestion_primary.amount)
                    st.rerun()
            else:
                st.markdown(
                    "<p class='toolbar__helper' style='margin:0;'>Set OPENAI_API_KEY to show an AI recommendation here.</p>",
                    unsafe_allow_html=True,
                )

    left_col, right_col = st.columns([2, 1], gap="large")

    with left_col:
        ai_placeholder = st.empty()
        _render_ai_summary(None)

        st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
        render_recurring_charges(baseline["recurring"])

    with right_col:
        # Budget target card at the very top-right
        _render_budget_target_card()
        st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
        render_snapshot_card(baseline["snapshot"])
        st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
        budget_placeholder = st.empty()
        _render_budget_insights(baseline_budget)

    # Category and lower sections
    render_category_breakdown(baseline["category_summary"])

    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    week_col, subs_col = st.columns([1.4, 1], gap="large")
    with week_col:
        weekly_placeholder = st.empty()
        with weekly_placeholder.container():
            render_weekly_spend(baseline_weekly)
    with subs_col:
        render_subscriptions(baseline["subscriptions"])

    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    render_yearly_net_flow(baseline["net_flow"])

    # Trigger AI-dependent computations and refresh placeholders once ready
    with st.spinner("Generating AI insights…"):
        context = build_dashboard_context(
            transactions,
            start_date=start_date,
            end_date=end_date,
        )

    _render_ai_summary(context["ai_summary"])
    _render_budget_insights(context["budget"])

    weekly_placeholder.empty()
    with weekly_placeholder.container():
        render_weekly_spend(context["weekly_spend"])

    st.markdown("</main>", unsafe_allow_html=True)


__all__ = ["render_dashboard"]
