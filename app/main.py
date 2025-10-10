"""Streamlit application entrypoint (renamed from app.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.components.sample_data import load_demo_dashboard
from app.layout import render_dashboard
from app.theme import apply_theme


def main() -> None:
    """Entry point for the Streamlit app."""

    st.set_page_config(
        page_title="Spending Analyser",
        page_icon="💳",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_theme()

    demo = load_demo_dashboard()

    render_dashboard(
        ai_summary=demo.ai_summary,
        monthly_snapshot=demo.monthly_snapshot,
        budget_tracker=demo.budget_tracker,
        category_breakdown=demo.category_breakdown,
        subscriptions=demo.subscriptions,
        weekly_spend=demo.weekly_spend,
        recurring_charges=demo.recurring_charges,
        net_flow=demo.net_flow,
        default_date_range=demo.default_date_range,
    )


if __name__ == "__main__":
    main()
