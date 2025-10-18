"""Streamlit application entrypoint (renamed from app.py)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from datetime import date

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.layout import render_dashboard
from app.theme import apply_theme
from core.data_loader import load_transactions
from data.synth import write_transactions_csv

DATA_FIXTURE_PATH = PROJECT_ROOT / "data" / "fixtures" / "seed.csv"
AUTO_SYNTH_ENV = "SPENDING_ANALYSER_AUTO_SYNTH"


@st.cache_resource(show_spinner=False)
def _refresh_seed_dataset() -> Path:
    """Regenerate the synthetic transaction CSV once per server lifecycle."""

    toggle = os.getenv(AUTO_SYNTH_ENV)
    if toggle is not None and toggle.strip().lower() in {"0", "false", "no"}:
        return DATA_FIXTURE_PATH

    write_transactions_csv(path=str(DATA_FIXTURE_PATH))
    load_transactions.cache_clear()
    return DATA_FIXTURE_PATH


def _default_date_range(transactions: pd.DataFrame) -> tuple[date, date]:
    today = date.today()
    if transactions.empty or "date" not in transactions.columns:
        return today.replace(day=1), today

    date_series = pd.to_datetime(transactions["date"], errors="coerce").dropna()
    if date_series.empty:
        return today.replace(day=1), today

    latest = date_series.max()
    period = latest.to_period("M")
    start_of_month = period.start_time.date()
    end_of_month = min(period.end_time.date(), today)
    return start_of_month, end_of_month


def main() -> None:
    """Entry point for the Streamlit app."""

    st.set_page_config(
        page_title="Spending Analyser",
        page_icon="💳",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_theme()

    _refresh_seed_dataset()

    transactions = load_transactions()

    default_range = _default_date_range(transactions)

    render_dashboard(
        default_date_range=default_range,
        transactions=transactions,
    )


if __name__ == "__main__":
    main()
