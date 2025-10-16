"""Budget widgets: split into spend insights (metrics) and a thin controls card.

Previously this module rendered a single combined card. We now expose:
 - render_budget_spend_insights(tracker): right-column metrics only
 - render_budget_controls(tracker): thin card with target control + progress

Both parts share the same `monthly_budget_value` session key so they stay in sync.
"""

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
            <span>{_format_currency(spend)} vs {_format_currency(max(budget, 0))}</span>
          </div>
          <p class="progress__note">{note}</p>
        </div>
        """
    )


def _budget_spend_html(tracker: BudgetTracker, budget_value: float) -> str:
    # Use the user-chosen budget value for all calculations to keep the UI consistent
    budget = float(max(budget_value, 0.0))

    current_spend = float(tracker.current_spend)
    projected_spend = float(tracker.projected_or_actual_spend)

    # Status is based on projected position vs chosen budget
    projected_is_under = projected_spend <= budget if budget > 0 else False
    status_label = "Under budget" if projected_is_under else "Over budget"
    status_dot = "status-dot status--ok" if projected_is_under else "status-dot status--bad"

    spend_label = "Actual spend" if tracker.is_month_complete else "Projected spend"

    # Savings/overspend wording – avoid showing negative savings
    savings_amount = budget - projected_spend
    if tracker.is_month_complete:
        savings_label = "Savings" if savings_amount >= 0 else "Overspend"
    else:
        savings_label = "Projected savings" if savings_amount >= 0 else "Projected overspend"

    # Variance percentages vs chosen budget (guard divide by zero)
    if budget > 0:
        proj_var_pct = ((projected_spend - budget) / budget) * 100.0
        proj_var_text = _format_variance(proj_var_pct, is_under_budget=projected_is_under)

        actual_is_under = current_spend <= budget
        actual_var_pct = ((current_spend - budget) / budget) * 100.0
        actual_var_text = _format_variance(actual_var_pct, is_under_budget=actual_is_under)

        # Build chip content/classes for colored badges
        actual_chip_text, actual_chip_class = _chip_text(actual_var_text, actual_is_under)
        proj_chip_text, proj_chip_class = _chip_text(proj_var_text, projected_is_under)
    else:
        proj_var_text = "—"
        actual_var_text = "—"
        actual_chip_text = actual_var_text
        proj_chip_text = proj_var_text
        actual_chip_class = "chip"
        proj_chip_class = "chip"

    # Header becomes "Spend insights" (no controls wording)
    header_html = dedent(
        f"""
        <header class="budget-card__header">
          <div>
            <span class="pill">Spend insights</span>
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
            <span class="metric-value">{_format_currency(current_spend)}</span>
          </div>
          <div class="metric-block">
            <span class="metric-label">{escape(spend_label)}</span>
            <span class="metric-value">{_format_currency(projected_spend)}</span>
          </div>
          <div class="metric-block">
            <span class="metric-label">{escape(savings_label)}</span>
            <span class="metric-value">{_format_currency(abs(savings_amount))}</span>
          </div>
          <div class="metric-block">
            <span class="metric-label">Actual vs budget</span>
            <span class="metric-value"><span class="{actual_chip_class}">{actual_chip_text}</span></span>
          </div>
          <div class="metric-block">
            <span class="metric-label">Projected vs budget</span>
            <span class="metric-value"><span class="{proj_chip_class}">{proj_chip_text}</span></span>
          </div>
        </div>
        """
    )

    # Spend insights card (metrics only)
    return dedent(
        f"""
        <section class="card budget-card" role="region" aria-label="Budget spend insights">
          {header_html}
          {metrics_html}
        </section>
        """
    )

def _left_align_html(s: str) -> str:
    # prevent Markdown from turning indented HTML into a code block
    return "\n".join(line.lstrip() for line in s.splitlines())


def _get_budget_value(default_value: float) -> float:
  """Shared getter for the session-stored monthly budget value."""
  budget_key = "monthly_budget_value"
  if budget_key not in st.session_state:
    st.session_state[budget_key] = float(default_value)
  return float(st.session_state[budget_key])


def render_budget_spend_insights(tracker: BudgetTracker) -> None:
  """Render the metrics-only budget spend insights card (right column)."""
  chosen = _get_budget_value(tracker.allocated_budget)
  card_html = _budget_spend_html(tracker, chosen)
  st.markdown(_left_align_html(card_html), unsafe_allow_html=True)


def render_budget_controls(tracker: BudgetTracker) -> float:
  """Render a thin card with the monthly budget progress and current target.

  The target value is read from `st.session_state["monthly_budget_value"]`, which
  should be controlled by the dedicated input card in the layout.
  """
  chosen = _get_budget_value(tracker.allocated_budget)

  # Optionally adjust projections if the user chose to exclude upcoming charges
  projected_value = float(tracker.projected_or_actual_spend)
  if bool(st.session_state.get("exclude_upcoming_from_projections", False)):
    adjustment = float(st.session_state.get("exclude_upcoming_adjustment", 0.0))
    projected_value = max(0.0, projected_value - max(0.0, adjustment))

  progress_html = _progress_block(projected_value, chosen)
  card_html = dedent(
    f"""
    <section class="card budget-controls-card" role="region" aria-label="Budget insights">
      <div class="budget-card__control">
      <span class="budget-card__control-title">Monthly budget</span>
      <div class="budget-card__control-readout">Target: {_format_currency(chosen)}</div>
      </div>
      {progress_html}
      <footer class="budget-card__footer">
      <span>Allocation</span>
      <span>{_format_currency(chosen)} target</span>
      </footer>
    </section>
    """
  )
  st.markdown(_left_align_html(card_html), unsafe_allow_html=True)
  return chosen


__all__ = [
  "render_budget_spend_insights",
  "render_budget_controls",
]
