"""Subscriptions tracker components rendered inside a self-contained app-card.

Matches the "Spend by week" card styling and isolation by using a scoped CSS
block and a single components.html render. This ensures the white card with
rounded corners and shadow renders consistently across pages.
"""

from __future__ import annotations

from html import escape
import streamlit as st
import streamlit.components.v1 as components
from core.models import Subscription, SubscriptionTracker


def render_subscriptions(tracker: SubscriptionTracker) -> None:
    """Render a card with subscription breakdown using the shared app-card box."""

    # Scoped CSS for the card and the subscriptions table (copied from Weekly Spend with small tweaks)
    _CARD_CSS = """
    <style>
    .app-card{background:#fff;border-radius:1.25rem;padding:1.5rem;border:1px solid rgba(148,163,184,.16);
      box-shadow:0 18px 36px rgba(15,23,42,.08)}
    .app-card__header{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem}
    .pill{display:inline-flex;align-items:center;padding:.35rem .8rem;border-radius:999px;
      background:rgba(37,99,235,.10);font-size:.72rem;font-weight:600;letter-spacing:.06em;
      text-transform:uppercase;color:#2563eb}
    .app-card__title{margin:.35rem 0 0;font-size:1.25rem;font-weight:600;color:#0f172a}

    .subscriptions-card__totals{display:flex;flex-direction:column;align-items:flex-end;gap:.2rem}
    .subscriptions-card__totals span{font-weight:700;color:#0f172a}
    .subscriptions-card__totals small{color:rgba(15,23,42,.65)}

    .table-list{margin-top:1rem;display:grid;gap:.5rem}
    .table-list__header,.table-list__row{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:.75rem;align-items:center}
    .table-list__header{padding:.65rem .25rem;border-bottom:1px solid #e6eef7;font-weight:600;color:#475569}
    .table-list__row{padding:.75rem .25rem;border-bottom:1px dashed #eef2f7;color:#0f172a}
    .table-list__row:last-child{border-bottom:none}
    .table-list__row span:nth-child(2),.table-list__row span:nth-child(3){color:#64748b}
    .table-list__row span:nth-child(4){text-align:right;font-weight:700}
    .table-list__empty{padding:1rem .25rem;color:#64748b}
    </style>
    """

    # Build rows
    if tracker.subscriptions:
        rows_html = "".join(
            (
                '<div class="table-list__row">'
                f'<span>{escape(sub.name)}</span>'
                f'<span>£{sub.monthly_cost:,.0f}</span>'
                f'<span>{sub.months_active}</span>'
                f'<span>£{sub.cumulative_cost:,.0f}</span>'
                '</div>'
            )
            for sub in tracker.subscriptions
        )
    else:
        rows_html = (
            '<div class="table-list__empty">'
            'No recurring subscriptions detected in the selected period.'
            '</div>'
        )

    html = _CARD_CSS + (
        '<div class="app-card subscriptions-card">'
        '  <div class="app-card__header">'
        '    <div>'
        f'      <div class="pill">{escape(tracker.subtitle)}</div>'
        f'      <h3 class="app-card__title">{escape(tracker.title)}</h3>'
        '    </div>'
        '    <div class="subscriptions-card__totals">'
        f'      <span>£{tracker.total_monthly:,.0f}/mo</span>'
        f'      <small>£{tracker.total_cumulative:,.0f} lifetime</small>'
        '    </div>'
        '  </div>'
        '  <div class="table-list table-list--subscriptions">'
        '    <div class="table-list__header">'
        '      <span>Service</span><span>Monthly</span><span>Months</span><span>Total</span>'
        '    </div>'
        f'    {rows_html}'
        '  </div>'
        '</div>'
    )

    # Estimate height (header + table rows + padding) so shadow isn't clipped
    row_count = max(1, len(tracker.subscriptions))
    est_height = 200 + 58 * row_count
    components.html(html, height=est_height, scrolling=False)


__all__ = ["Subscription", "SubscriptionTracker", "render_subscriptions"]
