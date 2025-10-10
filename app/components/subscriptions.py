"""Subscriptions tracker components."""

from __future__ import annotations

from html import escape
import streamlit as st
from core.models import Subscription, SubscriptionTracker


def render_subscriptions(tracker: SubscriptionTracker) -> None:
    """Render a card with subscription breakdown (single, flush-left HTML block)."""

    header_html = (
        '<div class="app-card subscriptions-card">'
        '<div class="app-card__header">'
        '<div>'
        f'<div class="pill">{escape(tracker.subtitle)}</div>'
        f'<h3 style="margin:0.35rem 0 0; font-size:1.4rem; font-weight:600;">{escape(tracker.title)}</h3>'
        '</div>'
        '<div class="subscriptions-card__totals">'
        f'<span>£{tracker.total_monthly:,.0f}/mo</span>'
        f'<small>£{tracker.total_cumulative:,.0f} lifetime</small>'
        '</div>'
        '</div>'
        '<div class="table-list table-list--subscriptions">'
        '<div class="table-list__header">'
        '<span>Service</span><span>Monthly</span><span>Months</span><span>Total</span>'
        '</div>'
    )

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

    html = header_html + rows_html + '</div></div>'

    # Single render call so it stays inside the same styled card/container
    st.markdown(html, unsafe_allow_html=True)


__all__ = ["Subscription", "SubscriptionTracker", "render_subscriptions"]
