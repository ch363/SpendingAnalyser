"""Data aggregation helpers for dashboard summaries."""

from __future__ import annotations

from datetime import date, timedelta
import re

import pandas as pd

from .models import CategorySpend, CategorySummary, MerchantSpend


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _normalise_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    if "is_refund" not in frame.columns:
        frame["is_refund"] = False
    # Ensure category column exists for downstream grouping
    if "category" not in frame.columns:
        frame["category"] = "uncategorised"
    return frame


def _range_dates(start: date, end: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if start_ts > end_ts:
        start_ts, end_ts = end_ts, start_ts
    return start_ts, end_ts


def _previous_period(start: pd.Timestamp, end: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    delta = end - start
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - delta
    return pd.Timestamp(previous_start.date()), pd.Timestamp(previous_end.date())


def _build_merchant_breakdown(category_frame: pd.DataFrame) -> tuple[MerchantSpend, ...]:
    if category_frame.empty:
        return ()

    spend_col = category_frame["spend"]
    total = float(spend_col.sum()) or 1.0

    merchants = category_frame.groupby("merchant", dropna=False)["spend"].sum().sort_values(ascending=False)

    top_merchants = []
    for merchant_name, amount in merchants.head(5).items():
        label = merchant_name if isinstance(merchant_name, str) and merchant_name else "Other"
        top_merchants.append(
            MerchantSpend(
                name=label,
                amount=float(amount),
                share=_safe_ratio(float(amount), total),
            )
        )

    return tuple(top_merchants)


def _group_by_category(frame: pd.DataFrame) -> pd.Series:
    return frame.groupby("category", dropna=False)["spend"].sum()


def _normalise_category_name(value: object) -> str:
    """Clean raw category strings to a consistent display label.

    Rules:
    - Treat None/NaN/empty as empty string (handled upstream as Uncategorised)
    - Replace underscores and non-alphanumeric groups with a single space
    - Collapse multiple spaces
    - Lowercase then Title Case for human-friendly labels
    - Special-case 'uncategorised/uncategorized' -> 'Uncategorised'
    """

    if value is None:
        return ""

    s = str(value)
    if not s or s.strip().lower() in {"nan", "none"}:
        return ""

    # Replace any run of non-alphanumerics with a space (handles underscores and odd spacing)
    s = re.sub(r"[^A-Za-z0-9]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    if not s:
        return ""
    if s in {"uncategorised", "uncategorized"}:
        return "Uncategorised"
    return s.title()


def build_category_summary(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    title: str = "Category split",
    subtitle: str = "Where money went",
) -> CategorySummary:
    """Aggregate category level spend for the supplied date window."""

    if transactions.empty:
        return CategorySummary(
            title=title,
            subtitle=subtitle,
            start_date=start_date,
            end_date=end_date,
            total_amount=0.0,
            categories=(),
        )

    frame = _normalise_dataframe(transactions)

    current_start, current_end = _range_dates(start_date, end_date)
    prev_start, prev_end = _previous_period(current_start, current_end)

    date_series = pd.to_datetime(frame["date"], errors="coerce")

    mask_current = (date_series >= current_start) & (date_series <= current_end)
    mask_previous = (date_series >= prev_start) & (date_series <= prev_end)

    current = frame.loc[mask_current].copy()
    previous = frame.loc[mask_previous].copy()

    current = current[(current["amount"] < 0) & (~current["is_refund"])].copy()
    previous = previous[(previous["amount"] < 0) & (~previous["is_refund"])].copy()

    current["spend"] = current["amount"].abs()
    previous["spend"] = previous["amount"].abs()

    total_spend = float(current["spend"].sum())
    if total_spend <= 0:
        return CategorySummary(
            title=title,
            subtitle=subtitle,
            start_date=start_date,
            end_date=end_date,
            total_amount=0.0,
            categories=(),
        )

    # Build normalised category labels for consistent grouping and display
    current["category_norm"] = current["category"].apply(_normalise_category_name)
    previous["category_norm"] = previous["category"].apply(_normalise_category_name)

    current_totals = current.groupby("category_norm", dropna=False)["spend"].sum()
    previous_totals = previous.groupby("category_norm", dropna=False)["spend"].sum()

    categories: list[CategorySpend] = []
    for category_name, amount in current_totals.sort_values(ascending=False).items():
        amount_value = float(amount)
        previous_amount = float(previous_totals.get(category_name, 0.0))
        change_amount = amount_value - previous_amount
        change_pct = _safe_ratio(change_amount, previous_amount) if previous_amount else 0.0

        # Merchant breakdown uses the same normalized label filter
        merchants = _build_merchant_breakdown(current[current["category_norm"] == category_name])

        name_str = "" if category_name is None else str(category_name)
        label = name_str or "Uncategorised"

        categories.append(
            CategorySpend(
                name=label,
                amount=amount_value,
                share=_safe_ratio(amount_value, total_spend),
                previous_amount=previous_amount,
                change_amount=change_amount,
                change_pct=change_pct,
                merchants=merchants,
            )
        )

    return CategorySummary(
        title=title,
        subtitle=subtitle,
        start_date=start_date,
        end_date=end_date,
        total_amount=total_spend,
        categories=tuple(categories),
    )


__all__ = ["build_category_summary"]
