"""Subscriptions tracker components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import streamlit as st


@dataclass(frozen=True)
class Subscription:
    name: str
    monthly_cost: float
    months_active: int

    @property
    def cumulative_cost(self) -> float:
        return self.monthly_cost * self.months_active


@dataclass(frozen=True)
class SubscriptionTracker:
    title: str
    subtitle: str
    subscriptions: Sequence[Subscription]
    total_monthly: float
    total_cumulative: float


def render_subscriptions(tracker: SubscriptionTracker) -> None:
    """Render a card with subscription breakdown."""

    with st.container():
        st.markdown("<div class='app-card subscriptions-card'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="app-card__header">
                <div>
                    <div class="pill">{tracker.subtitle}</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{tracker.title}</h3>
                </div>
                <div class="subscriptions-card__totals">
                    <span>£{tracker.total_monthly:,.0f}/mo</span>
                    <small>£{tracker.total_cumulative:,.0f} lifetime</small>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='table-list table-list--subscriptions'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="table-list__header">
                <span>Service</span>
                <span>Monthly</span>
                <span>Months</span>
                <span>Total</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for sub in tracker.subscriptions:
            st.markdown(
                f"""
                <div class="table-list__row">
                    <span>{sub.name}</span>
                    <span>£{sub.monthly_cost:,.0f}</span>
                    <span>{sub.months_active}</span>
                    <span>£{sub.cumulative_cost:,.0f}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


__all__ = ["Subscription", "SubscriptionTracker", "render_subscriptions"]
