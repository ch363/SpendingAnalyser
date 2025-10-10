"""High-level dashboard analytics built from transaction history."""

from __future__ import annotations

from datetime import date
from typing import Iterable, Sequence, TypedDict, cast

import pandas as pd

from core.models import (
    AISummary,
    BudgetTracker,
    CategorySummary,
    MonthlyFlow,
    MonthlySnapshot,
    NetFlowSeries,
    RecurringCharge,
    RecurringChargesTracker,
    Subscription,
    SubscriptionTracker,
    WeeklySpendPoint,
    WeeklySpendSeries,
)
class DashboardContext(TypedDict):
    snapshot: MonthlySnapshot
    budget: BudgetTracker
    category_summary: CategorySummary
    ai_summary: AISummary
    weekly_spend: WeeklySpendSeries
    subscriptions: SubscriptionTracker
    recurring: RecurringChargesTracker
    net_flow: NetFlowSeries

from core.summary_service import build_category_summary

from .monthly_overview import build_budget_tracker, build_monthly_snapshot
from .recurring import RecurringEntry, detect_recurring_transactions


def _ensure_frame(transactions: pd.DataFrame) -> pd.DataFrame:
    frame = transactions.copy()
    if frame.empty:
        return frame

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    frame = frame.dropna(subset=["date", "amount"])

    if "merchant" not in frame.columns and "description" in frame.columns:
        frame["merchant"] = frame["description"]
    if "description" not in frame.columns and "merchant" in frame.columns:
        frame["description"] = frame["merchant"]

    if "category" not in frame.columns:
        frame["category"] = "uncategorised"
    else:
        frame["category"] = frame["category"].fillna("uncategorised")

    if "is_refund" not in frame.columns:
        frame["is_refund"] = False

    frame = frame.sort_values("date").reset_index(drop=True)
    return frame


def _reference_day(frame: pd.DataFrame) -> pd.Timestamp:
    if frame.empty:
        return pd.Timestamp(date.today())
    return pd.Timestamp(frame["date"].max()).normalize()


def build_weekly_spend_series(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
) -> WeeklySpendSeries:
    frame = _ensure_frame(transactions)
    if frame.empty:
        return WeeklySpendSeries("Spend by week", "Recent weeks", ())

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    if end_ts < start_ts:
        start_ts, end_ts = end_ts, start_ts

    expenses = frame[(frame["amount"] < 0) & (~frame["is_refund"])].copy()
    if expenses.empty:
        return WeeklySpendSeries("Spend by week", "Recent weeks", ())

    expenses = expenses[(expenses["date"] >= start_ts) & (expenses["date"] <= end_ts)]
    expenses["week"] = expenses["date"].dt.to_period("W-SUN")
    weekly_totals = expenses.groupby("week")["amount"].sum().sort_index().abs()

    points: list[WeeklySpendPoint] = []
    for period_key, value in weekly_totals.items():
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="W-SUN")
        amount = float(value)
        week_start = period.start_time
        week_number = week_start.isocalendar().week
        label = f"Week {week_number:02d}"
        points.append(WeeklySpendPoint(week_label=label, amount=amount))

    return WeeklySpendSeries(
        title="Spend by week",
        subtitle=f"{len(points)} week{'s' if len(points) != 1 else ''} selected",
        points=tuple(points),
    )


def build_net_flow_series(
    transactions: pd.DataFrame,
    *,
    reference_date: date | None = None,
    months: int = 12,
) -> NetFlowSeries:
    frame = _ensure_frame(transactions)
    if frame.empty:
        return NetFlowSeries("Yearly net flow", str(date.today().year), ())

    ref = pd.Timestamp(reference_date or frame["date"].max()).normalize()
    end_period = ref.to_period("M")
    start_period = (end_period - (months - 1)) if months > 1 else end_period

    period_index = pd.period_range(start=start_period, end=end_period, freq="M")

    frame["month_period"] = frame["date"].dt.to_period("M")
    inflow_raw = frame.loc[frame["amount"] > 0].groupby("month_period")["amount"].sum()
    outflow_raw = frame.loc[frame["amount"] < 0].groupby("month_period")["amount"].sum()
    inflow: dict[pd.Period, float] = {}
    for period_key, amount in inflow_raw.items():
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="M")
        inflow[period] = float(amount)

    outflow: dict[pd.Period, float] = {}
    for period_key, amount in outflow_raw.items():
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="M")
        outflow[period] = float(amount)

    months_data: list[MonthlyFlow] = []
    for period in period_index:
        inflow_value = inflow.get(period, 0.0)
        outflow_value = outflow.get(period, 0.0)
        months_data.append(
            MonthlyFlow(
                month=period.strftime("%b"),
                inflow=inflow_value,
                outflow=abs(outflow_value),
            )
        )

    year_label = f"{period_index[0].strftime('%Y')} – {period_index[-1].strftime('%Y')}" if len(period_index) > 1 else period_index[0].strftime("%Y")
    return NetFlowSeries(
        title="Yearly net flow",
        subtitle=year_label,
        months=tuple(months_data),
    )


def _status_from_days(days_until_due: int) -> str:
    if days_until_due < 0:
        return "Overdue"
    if days_until_due <= 3:
        return "Due soon"
    return "Up to date"


def _build_recurring_entries(
    transactions: pd.DataFrame,
    *,
    reference_date: date | None = None,
) -> list[RecurringEntry]:
    frame = _ensure_frame(transactions)
    if frame.empty:
        return []

    expenses = frame[(frame["amount"] < 0) & (~frame["is_refund"])].copy()
    if expenses.empty:
        return []

    expenses["spend"] = expenses["amount"].abs()
    expenses["description"] = expenses["merchant"]

    today = pd.Timestamp(reference_date or frame["date"].max()).normalize()
    return detect_recurring_transactions(expenses, today=today, amount_tolerance=0.1, min_occurrences=3)


def build_subscription_tracker(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    reference_date: date | None = None,
    top_n: int = 6,
) -> SubscriptionTracker:
    entries = _build_recurring_entries(transactions, reference_date=reference_date)
    allowed_categories = {
        "subscriptions",
        "entertainment",
        "fitness",
        "software",
        "news",
        "education",
        "services",
    }
    monthly_entries = [
        entry
        for entry in entries
        if entry["interval_days"] >= 28
        and entry.get("category", "").lower() in allowed_categories
    ]
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)

    subscriptions: list[Subscription] = []
    current_period_entries = [
        entry
        for entry in monthly_entries
        if start_ts <= entry["last_date"].normalize() <= end_ts
    ]

    if current_period_entries:
        relevant_entries = current_period_entries
    else:
        relevant_entries = monthly_entries
    sorted_monthlies = sorted(
        relevant_entries,
        key=lambda item: float(cast(float, item["average_amount"])),
        reverse=True,
    )
    for entry in sorted_monthlies[:top_n]:
        monthly_cost = float(entry["average_amount"])
        if monthly_cost <= 0:
            continue
        months_active = int(entry["occurrences"])
        subscriptions.append(
            Subscription(
                name=str(entry["merchant"]),
                monthly_cost=monthly_cost,
                months_active=max(months_active, 1),
            )
        )

    total_monthly = sum(sub.monthly_cost for sub in subscriptions)
    total_cumulative = sum(sub.cumulative_cost for sub in subscriptions)

    return SubscriptionTracker(
        title="Subscriptions tracker",
        subtitle="Recurring services",
        subscriptions=tuple(subscriptions),
        total_monthly=total_monthly,
        total_cumulative=total_cumulative,
    )


def build_recurring_charges_tracker(
    transactions: pd.DataFrame,
    *,
    reference_date: date | None = None,
    top_n: int = 5,
) -> RecurringChargesTracker:
    entries = _build_recurring_entries(transactions, reference_date=reference_date)
    if not entries:
        return RecurringChargesTracker("Recurring charges", "Upcoming", ())

    sorted_entries = sorted(
        entries,
        key=lambda item: (int(item["days_until_due"]), -float(item["average_amount"])),
    )

    charges: list[RecurringCharge] = []
    for entry in sorted_entries[:top_n]:
        amount = float(entry["average_amount"])
        if amount <= 0:
            continue
        next_date = entry["next_date"]
        next_label = pd.Timestamp(next_date).strftime("%d %b") if next_date is not None else "TBC"
        cadence = str(entry["interval_label"])
        status = _status_from_days(int(entry["days_until_due"]))
        charges.append(
            RecurringCharge(
                name=str(entry["merchant"]),
                amount=amount,
                cadence=cadence,
                next_date=next_label,
                status=status,
            )
        )

    return RecurringChargesTracker(
        title="Recurring charges",
        subtitle="Upcoming",
        charges=tuple(charges),
    )


def generate_ai_summary(
    *,
    snapshot: MonthlySnapshot,
    budget: BudgetTracker,
    category_summary: CategorySummary,
) -> AISummary:
    headline_direction = "under" if budget.is_under_budget else "over"
    gap_value = abs(budget.savings_projection)
    headline = (
        f"You're tracking {headline_direction} budget by £{gap_value:,.0f} "
        f"with a projected finish at £{budget.projected_or_actual_spend:,.0f}."
    )

    supporting: list[str] = []
    if category_summary.categories:
        top_category = category_summary.categories[0]
        supporting.append(
            f"{top_category.name} leads spend at £{top_category.amount:,.0f} "
            f"({top_category.share * 100:.1f}% of totals)."
        )
        if top_category.merchants:
            top_merchant = top_category.merchants[0]
            supporting.append(
                f"{top_merchant.name} alone accounts for £{top_merchant.amount:,.0f} "
                "this month."
            )
    if snapshot.metrics:
        primary = snapshot.metrics[0]
        delta_text = primary.delta if primary.delta else "no change vs prior period"
        supporting.append(f"Primary metric: {primary.label} is {primary.value} ({delta_text}).")

    focus_options = (
        "Stay on budget",
        "Tackle top categories",
        "Plan for recurring charges",
    )

    return AISummary(
        headline=headline,
        supporting_points=tuple(dict.fromkeys(supporting)),
        focus_options=focus_options,
        default_focus=focus_options[0],
    )


def build_dashboard_context(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
) -> DashboardContext:
    frame = _ensure_frame(transactions)

    snapshot = build_monthly_snapshot(frame, start_date=start_date, end_date=end_date)
    budget = build_budget_tracker(frame, start_date=start_date, end_date=end_date)
    category_summary = build_category_summary(
        frame,
        start_date=start_date,
        end_date=end_date,
        title="Category insight",
        subtitle="Where money went",
    )

    ai_summary = generate_ai_summary(snapshot=snapshot, budget=budget, category_summary=category_summary)
    weekly_spend = build_weekly_spend_series(
        frame,
        start_date=start_date,
        end_date=end_date,
    )
    subscriptions = build_subscription_tracker(
        frame,
        start_date=start_date,
        end_date=end_date,
        reference_date=end_date,
    )
    recurring = build_recurring_charges_tracker(frame, reference_date=end_date)
    net_flow = build_net_flow_series(frame, reference_date=end_date)

    return {
        "snapshot": snapshot,
        "budget": budget,
        "category_summary": category_summary,
        "ai_summary": ai_summary,
        "weekly_spend": weekly_spend,
        "subscriptions": subscriptions,
        "recurring": recurring,
        "net_flow": net_flow,
    }


__all__ = [
    "build_weekly_spend_series",
    "build_net_flow_series",
    "build_subscription_tracker",
    "build_recurring_charges_tracker",
    "generate_ai_summary",
    "build_dashboard_context",
    "DashboardContext",
]
