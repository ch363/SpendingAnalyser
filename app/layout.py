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
    render_budget_controls,
    render_budget_spend_insights,
    render_category_breakdown,
    render_recurring_charges,
    render_snapshot_card,
    render_subscriptions,
    render_weekly_spend,
    render_yearly_net_flow,
)
from analytics.dashboard import DashboardContext, build_dashboard_context
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
            selected_focus = st.segmented_control(
                "Insight focus",
                options=focus_options,
                default=current_focus if current_focus in focus_options else None,
                key="dashboard_ai_focus",
            )
            # Guarantee a string value for lookup
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

        st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
        render_recurring_charges(context["recurring"])
        # New thin budget insights card under recurring section
    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
    # (Cards moved to full-width row below)

    with right_col:
        render_snapshot_card(context["snapshot"])
        st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)
        render_budget_spend_insights(context["budget"])


    st.markdown("<div class='layout-gap'></div>", unsafe_allow_html=True)

    # Full-width row: first two wider than the last two
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    day_of_month = today.day
    budget_value = float(st.session_state.get("monthly_budget_value", context["budget"].allocated_budget))
    current_spend = float(context["budget"].current_spend)
    remaining = max(0.0, budget_value - current_spend)
    days_left = max(1, days_in_month - day_of_month)
    allowance = remaining / days_left
    avg_so_far = current_spend / max(1, day_of_month)
    target_pace = budget_value / max(1, days_in_month)
    on_track = avg_so_far <= target_pace

    # Uniform five-card row: input, monthly budget, allowance, pace, upcoming
    c_input, c_budget, c_daily, c_pace, c_upcoming = st.columns([1, 1, 1, 1, 1], gap="medium")

    # Input card (controls the shared monthly budget)
    with c_input:
        with st.container():
            # Scope marker to allow CSS to style this container as a single card
            st.markdown("<div class='budget-target-scope' style='display:none'></div>", unsafe_allow_html=True)
            budget_key = "monthly_budget_value"
            # Apply any AI-suggested value before the widget is created to avoid Streamlit state errors
            pending_key = "pending_budget_value"
            if pending_key in st.session_state:
                try:
                    st.session_state[budget_key] = float(st.session_state.pop(pending_key))
                except Exception:
                    st.session_state.pop(pending_key, None)
            if budget_key not in st.session_state:
                st.session_state[budget_key] = float(budget_value)
            value = st.number_input(
                "Budget target (£/month)",
                min_value=0.0,
                step=50.0,
                format="%.0f",
                key=budget_key,
                help="What‑if target used for progress, pace, and savings/overspend calculations.",
            )
            st.markdown("<div class='budget-card__control'>", unsafe_allow_html=True)
            st.markdown(
                "<p class='input-helper' style='margin:0;'>This updates all cards in this row.</p>",
                unsafe_allow_html=True,
            )

            # Small OpenAI-generated suggestion and one-liner rationale
            # Build a compact analytics snapshot for the model using available context
            suggestion_primary: BudgetSuggestion | None = None
            suggestion_alts: list[BudgetSuggestion] = []
            try:
                # Use values already computed above for consistency
                analytics_context = {
                    "current_spend": round(current_spend, 2),
                    "target_budget": round(float(st.session_state.get(budget_key, budget_value)), 2),
                    "days_in_month": days_in_month,
                    "day_of_month": day_of_month,
                    "avg_daily_spend_to_date": round(avg_so_far, 2),
                    "target_daily_pace": round(target_pace, 2),
                    "projected_or_actual_spend": round(float(context["budget"].projected_or_actual_spend), 2),
                    "is_month_complete": bool(context["budget"].is_month_complete),
                }
                primary, alts = generate_budget_suggestions(analytics_context=analytics_context)
                # Normalise
                suggestion_primary = BudgetSuggestion(primary.label, float(primary.amount), primary.rationale)
                suggestion_alts = [BudgetSuggestion(x.label, float(x.amount), x.rationale) for x in (alts or [])]
            except Exception:
                suggestion_primary = None
                suggestion_alts = []

            if suggestion_primary is not None:
                # Render suggestion and an apply button inside the same card
                st.markdown(
                    f"<p class='toolbar__helper' style='margin:0;'>AI suggestion: <strong>£{suggestion_primary.amount:,.0f}</strong> — {suggestion_primary.rationale}</p>",
                    unsafe_allow_html=True,
                )
                st.write("")  # subtle spacer
                if st.button(
                    f"Use {suggestion_primary.label} (£{suggestion_primary.amount:,.0f})",
                    key="apply_ai_budget_suggestion",
                    help="Apply the AI-recommended budget target",
                ):
                    # Defer applying the value until next rerun to avoid mutating widget key post-creation
                    st.session_state[pending_key] = float(suggestion_primary.amount)
                    st.rerun()
            else:
                st.markdown(
                    "<p class='toolbar__helper' style='margin:0;'>Set OPENAI_API_KEY to show an AI recommendation here.</p>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    with c_budget:
        render_budget_controls(context["budget"])

    with c_daily:
        chip = "chip chip--pos" if on_track else "chip chip--neg"
        st.markdown(
            dedent(
                f"""
                <section class=\"card budget-controls-card\"> 
                                    <div class=\"budget-card__header\" style=\"align-items:center; justify-content:space-between; gap:0.6rem;\"> 
                                        <span class=\"budget-card__control-title\">Daily allowance (to hit target)</span>
                    <span class=\"{chip}\">{'On-track' if on_track else 'Off-track'}</span>
                  </div>
                  <div style=\"display:grid; gap:0.35rem;\"> 
                    <div class=\"metric-value\" style=\"font-size:1.2rem;\">≤ £{allowance:,.0f}/day for the next {days_left} days</div>
                    <div class=\"toolbar__helper\">Avg so far £{avg_so_far:,.0f}/day · Target pace £{target_pace:,.0f}/day ({budget_value:,.0f}/{days_in_month})</div>
                  </div>
                </section>
                """
            ),
            unsafe_allow_html=True,
        )

    with c_pace:
        compare_target = target_pace
        pace_ratio = (avg_so_far / compare_target) if compare_target > 0 else 0.0
        pace_pct = (pace_ratio - 1.0) * 100.0
        bar_fill = max(0.0, min(1.5, pace_ratio)) * 100
        st.markdown(
            dedent(
                f"""
                <section class=\"card budget-controls-card\"> 
                  <div class=\"budget-card__header\" style=\"align-items:center; justify-content:space-between; gap:0.6rem;\"> 
                                        <span class=\"budget-card__control-title\">Spending pace vs target</span>
                  </div>
                  <div class=\"budget-progress\"> 
                    <div class=\"progress\" aria-hidden=\"true\"> 
                      <div class=\"progress__fill\" style=\"width: {bar_fill:.0f}%\"></div>
                    </div>
                    <div class=\"progress__legend\"><span>Avg £{avg_so_far:,.0f}/day</span><span>Target £{compare_target:,.0f}/day</span></div>
                    <p class=\"progress__note\">Pace {pace_pct:+.0f}% {'over' if pace_pct>0 else 'under'} target.</p>
                  </div>
                </section>
                """
            ),
            unsafe_allow_html=True,
        )

    with c_upcoming:
        upcoming_list = []
        try:
            charges = list(getattr(context["recurring"], "charges", []))
        except Exception:
            charges = []
        from datetime import datetime as _dt
        today_dt = _dt.today()
        cutoff = today_dt + timedelta(days=7)
        for ch in charges:
            next_str = getattr(ch, "next_date", "")
            try:
                nd = _dt.strptime(next_str, "%d %b").replace(year=today.year)
            except Exception:
                try:
                    nd = _dt.strptime(next_str, "%Y-%m-%d")
                except Exception:
                    continue
            if today_dt <= nd <= cutoff:
                amt = float(getattr(ch, "amount", 0.0))
                upcoming_list.append(f"{getattr(ch, 'name', 'Charge')} £{amt:,.0f} · due {nd.strftime('%d %b')}")
        items_html = "<br/>".join(upcoming_list[:4]) if upcoming_list else "No upcoming charges in next 7 days."
        st.markdown(
            dedent(
                f"""
                <section class=\"card budget-controls-card\"> 
                  <div class=\"budget-card__header\" style=\"align-items:center; justify-content:space-between; gap:0.6rem;\"> 
                    <span class=\"budget-card__control-title\">Upcoming charges (7 days)</span>
                  </div>
                  <div class=\"toolbar__helper\">{items_html}</div>
                </section>
                """
            ),
            unsafe_allow_html=True,
        )

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
