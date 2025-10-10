"""Recurring charges tracker component."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import streamlit as st


@dataclass(frozen=True)
class RecurringCharge:
    name: str
    amount: float
    cadence: str
    next_date: str
    status: str


@dataclass(frozen=True)
class RecurringChargesTracker:
    title: str
    subtitle: str
    charges: Sequence[RecurringCharge]


def render_recurring_charges(tracker: RecurringChargesTracker) -> None:
    """Render recurring charge list."""

    with st.container():
        st.markdown("<div class='app-card recurring-card'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="app-card__header">
                <div>
                    <div class="pill">{tracker.subtitle}</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{tracker.title}</h3>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='table-list table-list--recurring'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="table-list__header">
                <span>Charge</span>
                <span>Cadence</span>
                <span>Next</span>
                <span>Amount</span>
                <span>Status</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for charge in tracker.charges:
            st.markdown(
                f"""
                <div class="table-list__row">
                    <span>{charge.name}</span>
                    <span>{charge.cadence}</span>
                    <span>{charge.next_date}</span>
                    <span>£{charge.amount:,.0f}</span>
                    <span class="badge badge--{'ok' if charge.status == 'Up to date' else 'warn'}">{charge.status}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


__all__ = [
    "RecurringCharge",
    "RecurringChargesTracker",
    "render_recurring_charges",
]
