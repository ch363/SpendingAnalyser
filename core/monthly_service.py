"""Monthly overview analytics built from transaction data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Tuple

import pandas as pd

from .models import BudgetTracker, MonthlySnapshot, SnapshotMetric


@dataclass(frozen=True)
class MonthlyOverview:
    """Bundled result for snapshot and budget tracker outputs."""

    snapshot: MonthlySnapshot
    budget: BudgetTracker


def _ensure_datetime(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["date"] = pd.to_datetime(data.get("date"), errors="coerce")
    data["amount"] = pd.to_numeric(data.get("amount"), errors="coerce")
    if "is_refund" not in data.columns:
        data["is_refund"] = False
    else:
        data["is_refund"] = data["is_refund"].fillna(False)
    return data.dropna(subset=["date", "amount"])


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


def _format_currency(value: float) -> str:
    return f"£{value:,.0f}"


def _describe_period(start: pd.Timestamp, end: pd.Timestamp) -> Tuple[str, str]:
    same_month = start.month == end.month and start.year == end.year
    period_title = start.strftime("%B snapshot") if same_month else "Period snapshot"
    if same_month and start.day == 1 and end.day == end.days_in_month:
        label = start.strftime("%B %Y")
    else:
        label = f"{start.strftime('%d %b')} – {end.strftime('%d %b %Y')}"
    return period_title, label


def _build_snapshot_metrics(
    current: pd.DataFrame,
    previous: pd.DataFrame,
    period_start: pd.Timestamp,
    period_end: pd.Timestamp,
) -> Tuple[SnapshotMetric, ...]:
    spend_series = current["spend"] if "spend" in current else pd.Series(dtype=float)
    total_spend = float(spend_series.sum())

    prev_total = float(previous.get("spend", pd.Series(dtype=float)).sum())
    diff = total_spend - prev_total
    diff_label = "First month tracked" if prev_total == 0 else f"{'-' if diff <= 0 else '+'}{_format_currency(abs(diff))} vs last month"
    is_positive = prev_total == 0 or diff <= 0

    metrics = [
        SnapshotMetric(
            label="Total spend",
            value=_format_currency(total_spend),
            delta=diff_label,
            is_positive=is_positive,
        )
    ]

    if prev_total > 0:
        pct_change = ((total_spend - prev_total) / prev_total) * 100
        change_delta = "Improved vs last month" if pct_change <= 0 else "Higher spend than last month"
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
                    value=f"{_format_currency(float(daily.min()))} ({quiet_day.strftime('%d %b')})",
                )
            )
            metrics.append(
                SnapshotMetric(
                    label="Busiest day",
                    value=f"{_format_currency(float(daily.max()))} ({busy_day.strftime('%d %b')})",
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

    transaction_count = len(current)
    metrics.append(
        SnapshotMetric(
            label="Transactions",
            value=f"{transaction_count:,}",
        )
    )

    return tuple(metrics)


def build_monthly_snapshot(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
) -> MonthlySnapshot:
    frame = _ensure_datetime(transactions)
    start_ts, end_ts = _period_bounds(start_date, end_date)
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
    metrics = _build_snapshot_metrics(current, previous, start_ts, end_ts)

    return MonthlySnapshot(title=title, period_label=label, metrics=metrics)


def _monthly_spend_history(frame: pd.DataFrame) -> pd.Series:
    spend = frame[(frame["amount"] < 0) & (~frame["is_refund"])].copy()
    if spend.empty:
        return pd.Series(dtype=float)
    spend["spend"] = spend["amount"].abs()
    return spend.groupby(spend["date"].dt.to_period("M"))["spend"].sum().sort_index()


def _estimate_budget(frame: pd.DataFrame, current_period: pd.Period) -> float:
    history = _monthly_spend_history(frame)
    if current_period in history.index:
        history = history.drop(index=current_period)
    if history.empty:
        fallback = 3000.0
        return fallback
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
    frame = _ensure_datetime(transactions)
    start_ts, end_ts = _period_bounds(start_date, end_date)

    current_period = start_ts.to_period("M")
    current_mask = (frame["date"] >= start_ts) & (frame["date"] <= end_ts)
    current = frame.loc[current_mask].copy()
    current = current[(current["amount"] < 0) & (~current["is_refund"])].copy()
    current["spend"] = current["amount"].abs()

    total_spend = float(current["spend"].sum())
    data_end = frame["date"].max().date() if not frame.empty else end_date

    days_in_period = (end_ts - start_ts).days + 1
    covered_end = min(end_ts.normalize().date(), data_end)
    covered_days = (pd.Timestamp(covered_end) - start_ts).days + 1
    if covered_days <= 0:
        covered_days = max(1, days_in_period)

    period_obj = start_ts.to_period("M")
    month_days = period_obj.days_in_month if start_ts.month == end_ts.month else days_in_period

    is_month_complete = end_ts.date() >= period_obj.end_time.date() and data_end >= period_obj.end_time.date()

    if is_month_complete or covered_days >= month_days:
        projected = total_spend
    else:
        daily_average = total_spend / max(covered_days, 1)
        projected = daily_average * month_days

    budget_value = baseline_budget if baseline_budget is not None else _estimate_budget(frame, current_period)
    if budget_value <= 0:
        budget_value = 3000.0

    savings_projection = budget_value - projected
    variance_percent = ((projected - budget_value) / budget_value) * 100 if budget_value else 0.0
    under_budget = projected <= budget_value

    return BudgetTracker(
        title="Budget tracking",
        current_spend=total_spend,
        projected_or_actual_spend=projected,
        savings_projection=savings_projection,
        variance_percent=variance_percent,
        allocated_budget=budget_value,
        is_under_budget=under_budget,
        is_month_complete=is_month_complete,
    )


__all__ = [
    "MonthlyOverview",
    "build_monthly_snapshot",
    "build_budget_tracker",
]
