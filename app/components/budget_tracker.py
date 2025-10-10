"""Budget tracking component for the dashboard scaffold."""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class BudgetTracker:
    title: str
    current_spend: float
    projected_or_actual_spend: float
    savings_projection: float
    variance_percent: float
    allocated_budget: float
    is_under_budget: bool
    is_month_complete: bool


def _format_currency(value: float) -> str:
    return f"£{value:,.0f}"


def render_budget_tracker(tracker: BudgetTracker) -> float:
    """Render budget tracker card and return the updated budget value."""

    budget_key = "monthly_budget_value"
    current_budget = st.session_state.get(budget_key, tracker.allocated_budget)

    indicator_class = (
        "budget-status__dot budget-status__dot--ontrack"
        if tracker.is_under_budget
        else "budget-status__dot budget-status__dot--offtrack"
    )
    indicator_label = "Under budget" if tracker.is_under_budget else "Over budget"

    spend_label = "Actual spend" if tracker.is_month_complete else "Projected spend"
    savings_label = "Savings" if tracker.is_month_complete else "Projected savings"
    variance_value = f"{abs(tracker.variance_percent):.1f}%"
    variance_delta = "Under budget" if tracker.is_under_budget else "Over budget"
    variance_sign = "-" if tracker.is_under_budget else "+"

    with st.container():
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="app-card__header">
                <div>
                    <div class="pill">Budget & controls</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">
                        {tracker.title}
                    </h3>
                </div>
                <div class="budget-status__indicator">
                    <span class="{indicator_class}"></span>
                    <span>{indicator_label}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metrics = st.columns(4)
        metrics[0].metric("Current spend", _format_currency(tracker.current_spend))
        metrics[1].metric(spend_label, _format_currency(tracker.projected_or_actual_spend))
        metrics[2].metric(savings_label, _format_currency(tracker.savings_projection))
        metrics[3].metric(
            "% vs budget",
            f"{variance_sign}{variance_value}",
            delta=variance_delta,
        )

        st.markdown("<hr style='margin: 1.2rem 0; border: none; border-top: 1px solid var(--app-border);' />", unsafe_allow_html=True)

        updated_budget = st.number_input(
            "Monthly budget",
            min_value=0.0,
            value=float(current_budget),
            step=50.0,
            key=budget_key,
        )

        utilisation = 0
        if updated_budget > 0:
            utilisation = min(int((tracker.current_spend / updated_budget) * 100), 999)

        st.progress(min(utilisation, 100))

        st.markdown(
            f"""
            <div style='display:flex; justify-content: space-between; margin-top: 0.6rem; font-size: 0.85rem; color: var(--app-text-muted);'>
                <span>£0</span>
                <span>{_format_currency(updated_budget)} budget</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    return updated_budget


__all__ = ["BudgetTracker", "render_budget_tracker"]
