"""Budget tracking component for the dashboard scaffold."""

from __future__ import annotations

from textwrap import dedent

import streamlit as st

from core.models import BudgetTracker


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

    style_key = "budget_tracker_card_style_v4"
    if not st.session_state.get(style_key):
        st.markdown(
            """
            <style>
            div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="element-container"] .budget-card__sentinel),
            div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="element-container"] .budget-controls-card__sentinel) {
                background: rgba(255,255,255,0.96);
                border-radius: 1.5rem;
                padding: 1.9rem;
                box-shadow: 0 25px 45px rgba(15, 23, 42, 0.07);
                border: 1px solid rgba(148, 163, 184, 0.18);
            }
            div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="element-container"] .budget-controls-card__sentinel) {
                margin-top: 1.3rem;
            }
            .budget-card__content {
                display: flex;
                flex-direction: column;
                gap: 1.8rem;
            }
            .budget-card__header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1.5rem;
            }
            .budget-card__metrics {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 1.3rem;
            }
            .budget-card__metric {
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
            }
            .budget-card__metric-label {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--app-text-muted, #6b7280);
            }
            .budget-card__metric-value {
                font-size: 1.8rem;
                font-weight: 600;
                color: var(--app-text-strong, #0f172a);
            }
            .budget-card__chip {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                background: rgba(22, 163, 74, 0.12);
                color: #166534;
                border-radius: 999px;
                padding: 0.25rem 0.85rem;
                font-size: 0.8rem;
                font-weight: 600;
                margin-top: 0.4rem;
            }
            .budget-card__chip--negative {
                background: rgba(220, 38, 38, 0.12);
                color: #b91c1c;
            }
            .budget-controls-card__header h4 {
                margin: 0;
                font-size: 1.1rem;
                font-weight: 600;
                color: #0f172a;
            }
            .budget-controls-card__header p {
                margin: 0.4rem 0 0;
                font-size: 0.9rem;
                color: rgba(15, 23, 42, 0.6);
            }
            div[data-testid="stNumberInput"] label {
                display: none;
            }
            div[data-testid="stNumberInput"] input {
                border-radius: 0.9rem;
                border: 1px solid rgba(148, 163, 184, 0.45);
                padding: 0.65rem 1rem;
                font-weight: 600;
                font-size: 1rem;
                color: #0f172a;
                background: rgba(248, 250, 252, 0.9);
            }
            div[data-testid="stNumberInput"] button {
                background: rgba(15, 23, 42, 0.06);
                border: none;
                color: #0f172a;
                border-radius: 0.65rem;
            }
            div[data-testid="stNumberInput"] input:focus {
                border: 1px solid rgba(37, 99, 235, 0.45);
                outline: none;
                box-shadow: 0 0 0 2px rgba(37,99,235,0.08);
            }
            div[data-testid="stProgressBar"] > div > div {
                background: linear-gradient(90deg, #2563eb 0%, #38bdf8 100%);
            }
            div[data-testid="stProgressBar"] > div {
                background: rgba(37,99,235,0.15);
                border-radius: 999px;
            }
            .budget-controls-card__footer {
                display: flex;
                justify-content: space-between;
                margin-top: 0.65rem;
                font-size: 0.85rem;
                color: var(--app-text-muted, #6b7280);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state[style_key] = True

    with st.container():
        st.markdown("<div class='budget-card__sentinel'></div>", unsafe_allow_html=True)
        st.markdown(
            dedent(
                f"""
                <div class="budget-card__content">
                    <div class="budget-card__header">
                        <div>
                            <div class="pill">Budget & controls</div>
                            <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{tracker.title}</h3>
                        </div>
                        <div class="budget-status__indicator">
                            <span class="{indicator_class}"></span>
                            <span>{indicator_label}</span>
                        </div>
                    </div>
                    <div class="budget-card__metrics">
                        <div class="budget-card__metric">
                            <span class="budget-card__metric-label">Current spend</span>
                            <span class="budget-card__metric-value">{_format_currency(tracker.current_spend)}</span>
                        </div>
                        <div class="budget-card__metric">
                            <span class="budget-card__metric-label">{spend_label}</span>
                            <span class="budget-card__metric-value">{_format_currency(tracker.projected_or_actual_spend)}</span>
                        </div>
                        <div class="budget-card__metric">
                            <span class="budget-card__metric-label">{savings_label}</span>
                            <span class="budget-card__metric-value">{_format_currency(tracker.savings_projection)}</span>
                        </div>
                        <div class="budget-card__metric">
                            <span class="budget-card__metric-label">% vs budget</span>
                            <span class="budget-card__metric-value">{variance_sign}{variance_value}</span>
                            <span class="budget-card__chip{' budget-card__chip--negative' if not tracker.is_under_budget else ''}">{'↓' if tracker.is_under_budget else '↑'} {variance_delta}</span>
                        </div>
                    </div>
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

    with st.container():
        st.markdown("<div class='budget-controls-card__sentinel'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="budget-controls-card__header">
                <div>
                    <h4>Monthly budget</h4>
                    <p>Adjust your allowance and track utilisation instantly.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        updated_budget = st.number_input(
            "Monthly budget",
            min_value=0.0,
            value=float(current_budget),
            step=50.0,
            label_visibility="collapsed",
            key=budget_key,
        )

        utilisation = 0
        if updated_budget > 0:
            utilisation = min(int((tracker.current_spend / updated_budget) * 100), 999)

        st.progress(min(utilisation, 100))

        st.markdown(
            dedent(
                f"""
                <div class="budget-controls-card__footer">
                    <span>£0</span>
                    <span>{_format_currency(updated_budget)} budget</span>
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

    return updated_budget


__all__ = ["BudgetTracker", "render_budget_tracker"]
