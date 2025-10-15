"""Budget tracker card rendered in a single st.markdown via card_html,
mirroring the Monthly Snapshot pattern."""

from __future__ import annotations

from html import escape
from textwrap import dedent

import streamlit as st
from core.models import BudgetTracker


def _format_currency(value: float) -> str:
    return f"£{value:,.0f}"


def _format_variance(percent: float, *, is_under_budget: bool) -> str:
    sign = "-" if is_under_budget else "+"
    return f"{sign}{abs(percent):.1f}%"


def _chip_text(label: str, is_positive: bool) -> tuple[str, str]:
    chip_class = "chip chip--pos" if is_positive else "chip chip--neg"
    clean = label.strip()
    if clean and clean[0] in {"↑", "↓", "+", "-"}:
        return clean, chip_class
    prefix = "↓ " if is_positive else "↑ "
    return f"{prefix}{clean}".strip(), chip_class


def _progress_block(spend: float, budget: float) -> str:
    ratio = 0.0 if budget <= 0 else max(0.0, spend / max(budget, 1e-9))
    fill = min(ratio, 1.0) * 100
    overshoot = spend - budget
    if budget <= 0:
        note = "Assign a budget to start tracking utilisation."
    elif overshoot > 0:
        note = f"{_format_currency(overshoot)} over target"
    else:
        note = f"{_format_currency(abs(overshoot))} remaining"

    return dedent(
        f"""
        <div class="budget-progress" role="group" aria-label="Budget utilisation">
          <div class="progress" aria-hidden="true">
            <div class="progress__fill" style="width: {fill:.2f}%;"></div>
          </div>
          <div class="progress__legend">
            <span>{_format_currency(spend)} spent</span>
            <span>{_format_currency(max(budget, 0))} budget</span>
          </div>
          <p class="progress__note">{note}</p>
        </div>
        """
    )


def _budget_card_html(tracker: BudgetTracker, budget_value: float) -> str:
    status_label = "Under budget" if tracker.is_under_budget else "Over budget"
    status_dot = "status-dot status--ok" if tracker.is_under_budget else "status-dot status--bad"
    spend_label = "Actual spend" if tracker.is_month_complete else "Projected spend"
    savings_label = "Savings" if tracker.is_month_complete else "Projected savings"

    variance_text = _format_variance(
        tracker.variance_percent, is_under_budget=tracker.is_under_budget
    )
    variance_chip, variance_class = _chip_text(variance_text, tracker.is_under_budget)

    header_html = dedent(
        f"""
        <header class="budget-card__header">
          <div>
            <span class="pill">Budget &amp; controls</span>
            <h3 class="section-title">{escape(tracker.title)}</h3>
          </div>
          <div class="budget-card__status" aria-live="polite">
            <span class="{status_dot}" aria-hidden="true"></span>
            <span class="budget-card__status-label">{status_label}</span>
          </div>
        </header>
        """
    )

    metrics_html = dedent(
        f"""
        <div class="metrics budget-card__metrics">
          <div class="metric-block">
            <span class="metric-label">Current spend</span>
            <span class="metric-value">{_format_currency(tracker.current_spend)}</span>
          </div>
          <div class="metric-block">
            <span class="metric-label">{escape(spend_label)}</span>
            <span class="metric-value">{_format_currency(tracker.projected_or_actual_spend)}</span>
          </div>
          <div class="metric-block">
            <span class="metric-label">{escape(savings_label)}</span>
            <span class="metric-value">{_format_currency(tracker.savings_projection)}</span>
          </div>
          <div class="metric-block">
            <span class="metric-label">% vs budget</span>
            <span class="metric-value">{variance_text}</span>
            <span class="{variance_class}">{variance_chip}</span>
          </div>
        </div>
        """
    )

    progress_html = _progress_block(tracker.projected_or_actual_spend, budget_value)

    footer_html = dedent(
        f"""
        <footer class="budget-card__footer">
          <span>Allocation</span>
          <span>{_format_currency(budget_value)} target</span>
        </footer>
        """
    )

    # Single HTML blob, like Monthly Snapshot’s `card_html`
    return dedent(
        f"""
        <section class="card budget-card" role="region" aria-label="Budget tracker">
          {header_html}
          {metrics_html}
          <div class="budget-card__controls">
            <div class="budget-card__control">
              <span class="budget-card__control-title">Monthly budget</span>
              <p class="budget-card__control-helper">
                Adjust to explore different spending targets.
              </p>
              <!-- Note: the Streamlit number_input is rendered separately; this line is display-only -->
              <div class="budget-card__control-readout">Target: {_format_currency(budget_value)}</div>
            </div>
            {progress_html}
          </div>
          {footer_html}
        </section>
        """
    )

def _left_align_html(s: str) -> str:
    # prevent Markdown from turning indented HTML into a code block
    return "\n".join(line.lstrip() for line in s.splitlines())


def render_budget_tracker(tracker: BudgetTracker) -> float:
    """Render the budget card in one st.markdown call (like snapshot) and return the chosen budget."""
    budget_key = "monthly_budget_value"
    if budget_key not in st.session_state:
        st.session_state[budget_key] = float(tracker.allocated_budget)

    # 1) Read the control value first (widget can’t live *inside* the HTML card)
    chosen = st.number_input(
        "Monthly budget",
        min_value=0.0,
        value=float(st.session_state[budget_key]),
        step=50.0,
        format="%.0f",
        key=budget_key,
        label_visibility="collapsed",
    )
    chosen = float(chosen)

    # 2) Build one `card_html` string and render once (matches the Monthly Snapshot pattern)
    card_html = _budget_card_html(tracker, chosen)
    st.markdown(_left_align_html(card_html), unsafe_allow_html=True)

    return chosen


__all__ = ["render_budget_tracker"]
