"""Recurring charges tracker component rendered via components.html (single white card)."""

from __future__ import annotations

from html import escape
import streamlit.components.v1 as components

from core.models import RecurringCharge, RecurringChargesTracker
from app.theme import FONT_STACK


_CARD_CSS = """
<style>
:root, html, body {
  font-family: __FONT_STACK__;
}
body {
  margin: 0;
  color: #0f172a;
  background: transparent;
}
.app-card {
  background: #ffffff;
  border: 1px solid rgba(2, 6, 23, 0.06);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 1px 3px rgba(2, 6, 23, 0.06);
}
.app-card, .app-card * {
  font-family: inherit;
}
.app-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}
.pill {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.8rem;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.10);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #2563eb;
}
.app-card__title {
  margin: 0.35rem 0 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: #0f172a;
}
.table-list {
  margin-top: 1rem;
}
.table-list__header,
.table-list__row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
  gap: 8px;
  align-items: center;
}
.table-list__header {
  padding: 10px 0;
  border-bottom: 1px solid #e6eef7;
  font-weight: 600;
  color: #475569;
  font-size: 0.95rem;
}
.table-list__row {
  padding: 12px 0;
  border-bottom: 1px dashed #eef2f7;
  font-size: 0.95rem;
  color: #0f172a;
}
.table-list__row:last-child {
  border-bottom: none;
}
.table-list__row span:first-child {
  font-weight: 700;
}
.table-list__row span:nth-child(2),
.table-list__row span:nth-child(3) {
  color: #64748b;
}
.table-list__row span:nth-child(4) {
  text-align: right;
  font-weight: 700;
}
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.badge--ok {
  background: #ecfdf5;
  color: #065f46;
}
.badge--warn {
  background: #fef3c7;
  color: #92400e;
}
</style>
"""
_CARD_CSS = _CARD_CSS.replace("__FONT_STACK__", FONT_STACK)


def render_recurring_charges(tracker: RecurringChargesTracker) -> None:
    # Build table rows
    rows: list[str] = []
    for c in tracker.charges:
        status_text = (c.status or "").strip()
        status_class = "ok" if status_text.lower() == "up to date" else "warn"
        rows.append(
            f'<div class="table-list__row">'
            f'<span>{escape(c.name)}</span>'
            f'<span>{escape(c.cadence)}</span>'
            f'<span>{escape(str(c.next_date))}</span>'
            f'<span>£{c.amount:,.0f}</span>'
            f'<span class="badge badge--{status_class}">{escape(status_text)}</span>'
            f'</div>'
        )

    html = _CARD_CSS + f"""
<div class="app-card recurring-card">
  <div class="app-card__header">
    <div>
      <div class="pill">{escape(tracker.subtitle)}</div>
      <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{escape(tracker.title)}</h3>
    </div>
  </div>

  <div class="table-list table-list--recurring">
    <div class="table-list__header">
      <span>Charge</span><span>Cadence</span><span>Next</span><span>Amount</span><span>Status</span>
    </div>
    {''.join(rows)}
  </div>
</div>
"""

    # Estimate height to avoid clipping (header + rows).
    # Use a slightly tighter estimate so the card doesn't create excessive whitespace
    # between cards on the page.
    row_count = max(1, len(tracker.charges))
    est_height = 100 + 55 * row_count
    components.html(html, height=est_height, scrolling=False)


__all__ = [
    "RecurringCharge",
    "RecurringChargesTracker",
    "render_recurring_charges",
]
