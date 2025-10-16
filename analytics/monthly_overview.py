"""Monthly overview analytics derived from the transaction ledger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Tuple

import pandas as pd

from core.models import BudgetTracker, MonthlySnapshot, SnapshotMetric


@dataclass(frozen=True)
class MonthlyOverview:
    """Combined payload for snapshot and budget tracker widgets."""

    snapshot: MonthlySnapshot
    budget: BudgetTracker


def _ensure_frame(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()

    if "date" in data.columns:
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
    else:
        data["date"] = pd.NaT

    if "amount" in data.columns:
        data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    else:
        data["amount"] = 0.0

    data = data.dropna(subset=["date", "amount"])

    if "is_refund" not in data.columns:
        data["is_refund"] = False
    else:
        data["is_refund"] = data["is_refund"].fillna(False)

    return data


def _period_bounds(start: date, end: date) -> Tuple[pd.Timestamp, pd.Timestamp]:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if end_ts < start_ts:
        start_ts, end_ts = end_ts, start_ts
    return start_ts.normalize(), end_ts.normalize()


def _previous_period(start: pd.Timestamp, end: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    span = end - start
    prev_end = start - pd.Timedelta(days=1)
    prev_start = prev_end - span
    return prev_start.normalize(), prev_end.normalize()


def _previous_full_month_bounds(reference_start: pd.Timestamp) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """Return the first/last day of the previous full calendar month relative to ``reference_start``.

    Example: reference_start=2025-10-01 -> returns 2025-09-01 .. 2025-09-30
    """
    prev_period = (reference_start.to_period("M") - 1)
    return prev_period.start_time.normalize(), prev_period.end_time.normalize()


def _format_currency(value: float) -> str:
    return f"£{value:,.0f}"


def _describe_period(start: pd.Timestamp, end: pd.Timestamp) -> Tuple[str, str]:
    same_month = start.month == end.month and start.year == end.year
    full_month = start.day == 1 and end.day == end.days_in_month if same_month else False

    title = start.strftime("%B snapshot") if same_month else "Period snapshot"
    if full_month:
        label = start.strftime("%B %Y")
    else:
        label = f"{start.strftime('%d %b')} – {end.strftime('%d %b %Y')}"
    return title, label


def _build_snapshot_metrics(current: pd.DataFrame, previous: pd.DataFrame) -> Tuple[SnapshotMetric, ...]:
    spend_series = current["spend"] if "spend" in current else pd.Series(dtype=float)
    total_spend = float(spend_series.sum())

    prev_total = float(previous.get("spend", pd.Series(dtype=float)).sum())
    diff_cash = total_spend - prev_total
    if prev_total > 0:
        diff_label = f"{'-' if diff_cash <= 0 else '+'}{_format_currency(abs(diff_cash))} vs last month"
        is_positive = diff_cash <= 0
    else:
        diff_label = "First month tracked"
        is_positive = True

    metrics: list[SnapshotMetric] = [
        SnapshotMetric(
            label="Total spend",
            value=_format_currency(total_spend),
            delta=diff_label,
            is_positive=is_positive,
        )
    ]

    if prev_total > 0:
        pct_change = ((total_spend - prev_total) / prev_total) * 100
        change_delta = "Improved vs last month" if pct_change <= 0 else "Higher than last month"
        metrics.append(
            SnapshotMetric(
                label="Change vs last month",
                value=f"{pct_change:+.1f}%",
                delta=change_delta,
                is_positive=pct_change <= 0,
            )
        )
    else:
        metrics.append(
            SnapshotMetric(
                label="Change vs last month",
                value="—",
                delta="Limited history",
                is_positive=None,
            )
        )

    if not current.empty:
        daily = current.groupby(current["date"].dt.date)["spend"].sum()
        if not daily.empty:
            quiet_day = daily.idxmin()
            busy_day = daily.idxmax()
            metrics.append(
                SnapshotMetric(
                    label="Quietest day",
                    value=f"{_format_currency(float(daily.min()))} ({pd.Timestamp(quiet_day).strftime('%d %b')})",
                )
            )
            metrics.append(
                SnapshotMetric(
                    label="Busiest day",
                    value=f"{_format_currency(float(daily.max()))} ({pd.Timestamp(busy_day).strftime('%d %b')})",
                )
            )

    refund_mask = current[(current["amount"] > 0) | (current.get("is_refund", False) == True)]
    if not refund_mask.empty:
        refund_total = float(refund_mask["amount"].sum())
        metrics.append(
            SnapshotMetric(
                label="Refunds credited",
                value=_format_currency(refund_total),
            )
        )

    metrics.append(
        SnapshotMetric(
            label="Transactions",
            value=f"{len(current):,}",
        )
    )

    return tuple(metrics)


def _baseline_daily_spend(frame: pd.DataFrame, *, as_of: pd.Timestamp, lookback_days: int = 90) -> float | None:
    """Return median daily discretionary spend over the last ``lookback_days``.

    Rules:
    - Consider expenses only (amount < 0 and not refunds)
    - Exclude likely fixed charges (simple heuristic: categories like 'rent', 'mortgage', 'utilities', 'insurance')
    - Aggregate by calendar day and take median
    """
    if frame.empty:
        return None

    start = (as_of - pd.Timedelta(days=lookback_days - 1)).normalize()
    end = as_of.normalize()

    df = frame[(frame["date"] >= start) & (frame["date"] <= end)].copy()
    df = df[(df["amount"] < 0) & (~df["is_refund"])].copy()
    if df.empty:
        return None

    # Exclude fixed charges by category label when available
    if "category" in df.columns:
        fixed = {"rent", "mortgage", "utilities", "insurance", "council_tax", "taxes"}
        df = df[~df["category"].str.lower().isin(fixed)].copy()
        if df.empty:
            return None

    df["spend"] = df["amount"].abs()
    by_day = df.groupby(df["date"].dt.normalize())["spend"].sum()
    if by_day.empty:
        return None
    return float(by_day.median())


def _classify_against_baseline(current_total: float, start: pd.Timestamp, end: pd.Timestamp, baseline_daily: float | None) -> tuple[str, str]:
    """Return a label and tooltip comparing period spend to a daily baseline.

    Heuristic: expected spend = baseline_daily * number of covered days in period.
    Label buckets:
    - Below average: current <= 90% of expected
    - Normal for you: 90% < current < 110% of expected
    - Above average: current >= 110% of expected
    Tooltip explains baseline method.
    """
    default_tooltip = (
        "Median daily spend over last 90 days, excluding rent & other fixed charges"
    )
    if not baseline_daily or baseline_daily <= 0:
        return ("Normal for you", default_tooltip)

    days = (end.normalize() - start.normalize()).days + 1
    days = max(1, days)
    expected = baseline_daily * days
    if expected <= 0:
        return ("Normal for you", default_tooltip)

    ratio = current_total / expected
    if ratio <= 0.9:
        return ("Below average", default_tooltip)
    if ratio >= 1.1:
        return ("Above average", default_tooltip)
    return ("Normal for you", default_tooltip)


def build_monthly_snapshot(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
) -> MonthlySnapshot:
    frame = _ensure_frame(transactions)
    if frame.empty:
        return MonthlySnapshot(title="Snapshot", period_label="No data", metrics=())

    start_ts, end_ts = _period_bounds(start_date, end_date)
    # If the selection is a single calendar month (e.g., This month to date),
    # compare against the previous FULL calendar month. Otherwise, compare against
    # the immediately preceding span of equal length.
    if (start_ts.month == end_ts.month and start_ts.year == end_ts.year and start_ts.day == 1):
        prev_start, prev_end = _previous_full_month_bounds(start_ts)
    else:
        prev_start, prev_end = _previous_period(start_ts, end_ts)

    mask_current = (frame["date"] >= start_ts) & (frame["date"] <= end_ts)
    mask_previous = (frame["date"] >= prev_start) & (frame["date"] <= prev_end)

    current = frame.loc[mask_current].copy()
    previous = frame.loc[mask_previous].copy()

    current = current[(current["amount"] < 0) & (~current["is_refund"])].copy()
    previous = previous[(previous["amount"] < 0) & (~previous["is_refund"])].copy()

    current["spend"] = current["amount"].abs()
    previous["spend"] = previous["amount"].abs()

    title, label = _describe_period(start_ts, end_ts)
    metrics = _build_snapshot_metrics(current, previous)

    # Compute baseline vs period for the header badge
    as_of = min(end_ts, pd.Timestamp(frame["date"].max()).normalize()) if not frame.empty else end_ts
    baseline_daily = _baseline_daily_spend(frame, as_of=as_of, lookback_days=90)
    current_total = float(current["spend"].sum()) if "spend" in current else 0.0
    baseline_label, baseline_tooltip = _classify_against_baseline(current_total, start_ts, end_ts, baseline_daily)

    return MonthlySnapshot(
        title=title,
        period_label=label,
        metrics=metrics,
        baseline_label=baseline_label,
        baseline_tooltip=baseline_tooltip,
    )


def _monthly_spend_history(frame: pd.DataFrame) -> pd.Series:
    spend = frame[(frame["amount"] < 0) & (~frame["is_refund"])].copy()
    if spend.empty:
        return pd.Series(dtype=float)
    spend["spend"] = spend["amount"].abs()
    return spend.groupby(spend["date"].dt.to_period("M"))["spend"].sum().sort_index()


def _estimate_budget(frame: pd.DataFrame, current_period: pd.Period) -> float:
    history = _monthly_spend_history(frame)
    if current_period in history.index:
        history = history.loc[history.index != current_period]
    if history.empty:
        return 3000.0
    recent = history.tail(3)
    estimate = float(recent.mean())
    if estimate <= 0:
        return 3000.0
    return round(estimate / 50.0) * 50.0


def build_budget_tracker(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    baseline_budget: float | None = None,
) -> BudgetTracker:
    frame = _ensure_frame(transactions)
    if frame.empty:
        return BudgetTracker(
            title="Budget tracking",
            current_spend=0.0,
            projected_or_actual_spend=0.0,
            savings_projection=baseline_budget or 0.0,
            variance_percent=0.0,
            allocated_budget=baseline_budget or 0.0,
            is_under_budget=True,
            is_month_complete=False,
        )

    start_ts, end_ts = _period_bounds(start_date, end_date)

    current_period = start_ts.to_period("M")
    mask_current = (frame["date"] >= start_ts) & (frame["date"] <= end_ts)

    current = frame.loc[mask_current].copy()
    current = current[(current["amount"] < 0) & (~current["is_refund"])].copy()
    current["spend"] = current["amount"].abs()

    total_spend = float(current["spend"].sum())
    if frame["date"].empty:
        data_end = end_ts
    else:
        data_end = frame["date"].max()

    period_obj = start_ts.to_period("M")
    month_days = period_obj.days_in_month if start_ts.month == end_ts.month else (end_ts - start_ts).days + 1

    data_end_date = data_end.date()
    covered_end = min(end_ts.normalize().date(), data_end_date)
    covered_days = (pd.Timestamp(covered_end) - start_ts).days + 1
    covered_days = max(1, covered_days)

    if data_end_date >= period_obj.end_time.date() and covered_days >= month_days:
        projected = total_spend
        is_month_complete = True
    else:
        daily_average = total_spend / covered_days
        projected = daily_average * month_days
        is_month_complete = False

    budget_value = baseline_budget if baseline_budget is not None else _estimate_budget(frame, current_period)
    if budget_value <= 0:
        budget_value = 3000.0

    savings_projection = budget_value - projected
    variance_percent = ((projected - budget_value) / budget_value) * 100 if budget_value else 0.0
    is_under_budget = projected <= budget_value

    return BudgetTracker(
        title="Budget tracking",
        current_spend=total_spend,
        projected_or_actual_spend=projected,
        savings_projection=savings_projection,
        variance_percent=variance_percent,
        allocated_budget=budget_value,
        is_under_budget=is_under_budget,
        is_month_complete=is_month_complete,
    )


__all__ = [
    "MonthlyOverview",
    "build_monthly_snapshot",
    "build_budget_tracker",
]
