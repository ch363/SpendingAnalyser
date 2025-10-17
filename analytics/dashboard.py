"""High-level dashboard analytics built from transaction history."""

from __future__ import annotations

from datetime import date
from typing import Iterable, Mapping, Sequence, TypedDict, cast

import pandas as pd

from core.models import (
    AISummary,
    AISummaryFocus,
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
from core.ai.summary import SUMMARY_FOCUS_DEFINITIONS, build_focus_summaries
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

from .ai_forecasting import (
    WeeklyForecastRequest,
    WeeklyForecastResult,
    WeeklyHistoryRecord,
    forecast_weekly_spend,
)
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


def _weekly_history(
    frame: pd.DataFrame,
    *,
    start_ts: pd.Timestamp,
    months_back: int = 3,
) -> list[WeeklyHistoryRecord]:
    history_start = (start_ts - pd.DateOffset(months=months_back)).replace(day=1)
    history_end = start_ts - pd.Timedelta(days=1)

    history_df = frame[(frame["date"] >= history_start) & (frame["date"] <= history_end)].copy()
    if history_df.empty:
        return []

    history_df = history_df[(history_df["amount"] < 0) & (~history_df["is_refund"])].copy()
    if history_df.empty:
        return []

    history_df["week"] = history_df["date"].dt.to_period("W-SUN")
    weekly_totals = history_df.groupby("week")["amount"].sum().sort_index().abs()

    records: list[WeeklyHistoryRecord] = []
    month_counters: dict[tuple[int, int], int] = {}
    for period_key, value in weekly_totals.items():
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="W-SUN")
        start = period.start_time
        month_key = (start.year, start.month)
        month_counters[month_key] = month_counters.get(month_key, 0) + 1
        records.append(
            WeeklyHistoryRecord(
                week_of_month=month_counters[month_key],
                month=start.strftime("%B"),
                year=start.year,
                start_date=start.date().isoformat(),
                end_date=period.end_time.date().isoformat(),
                amount=float(value),
            )
        )
    return records


def _upcoming_week_requests(
    *,
    periods: Sequence[pd.Period],
    observed_cutoff: pd.Period | None,
    recurring_entries: Sequence[RecurringEntry],
    week_index_map: Mapping[pd.Period, int],
) -> list[WeeklyForecastRequest]:
    if not periods:
        return []

    recurring_summary: dict[pd.Period, float] = {}
    for entry in recurring_entries:
        next_date = entry.get("next_date")
        if next_date is None:
            continue
        week = pd.Timestamp(next_date).to_period("W-SUN")
        if week not in periods:
            continue
        recurring_summary[week] = recurring_summary.get(week, 0.0) + abs(float(entry.get("average_amount", 0.0)))

    requests: list[WeeklyForecastRequest] = []
    for period_key in periods:
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="W-SUN")
        # If we're currently mid-week, include this week in forecasts.
        # Only skip weeks strictly before the observed cutoff.
        if observed_cutoff is not None and period < observed_cutoff:
            continue

        start = period.start_time
        week_idx = week_index_map.get(period)
        if week_idx is None:
            continue
        requests.append(
            WeeklyForecastRequest(
                week_of_month=week_idx,
                start_date=start.date().isoformat(),
                end_date=period.end_time.date().isoformat(),
                recurring_commitments=recurring_summary.get(period, 0.0),
            )
        )
    return requests


def _format_week_label(period: pd.Period) -> str:
    """Format a W-SUN weekly period as a compact calendar range label.

    Examples:
    - Same month: 1–7 Oct
    - Cross month: 29 Sep–5 Oct
    - Cross year: 29 Dec 24–4 Jan 25
    """
    # Ensure we have a Period with weekly frequency
    week = period if isinstance(period, pd.Period) else pd.Period(str(period), freq="W-SUN")
    start = week.start_time.normalize()
    end = week.end_time.normalize()

    def _day_no_leading_zero(ts: pd.Timestamp) -> str:
        # Use platform-friendly no-leading-zero day; %-d not on Windows. Fallback strips leading 0.
        s = ts.strftime("%d")
        return s.lstrip("0") or "0"

    if start.year == end.year and start.month == end.month:
        # 1–7 Oct
        return f"{_day_no_leading_zero(start)}–{_day_no_leading_zero(end)} {end.strftime('%b')}"
    else:
        # 29 Sep–5 Oct (or include short years if different years)
        if start.year != end.year:
            return f"{_day_no_leading_zero(start)} {start.strftime('%b %y')}–{_day_no_leading_zero(end)} {end.strftime('%b %y')}"
        return f"{_day_no_leading_zero(start)} {start.strftime('%b')}–{_day_no_leading_zero(end)} {end.strftime('%b')}"


def build_weekly_spend_series(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    api_key: str | None = None,
) -> WeeklySpendSeries:
    frame = _ensure_frame(transactions)
    if frame.empty:
        return WeeklySpendSeries("Spend by week", "Recent weeks", ())

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    if end_ts < start_ts:
        start_ts, end_ts = end_ts, start_ts

    # Build weekly periods. If the selection falls within a single calendar month,
    # extend the range to cover the full month so we can forecast remaining weeks
    # (e.g., show Weeks 3 & 4 even when viewing month-to-date).
    same_month = start_ts.month == end_ts.month and start_ts.year == end_ts.year
    if same_month:
        month_period = start_ts.to_period("M")
        month_start = month_period.start_time
        month_end = month_period.end_time
        weekly_periods = pd.period_range(
            start=month_start.to_period("W-SUN"),
            end=month_end.to_period("W-SUN"),
            freq="W-SUN",
        )
        recurring_ref_date = month_end.date()
    else:
        weekly_periods = pd.period_range(start=start_ts.to_period("W-SUN"), end=end_ts.to_period("W-SUN"), freq="W-SUN")
        recurring_ref_date = end_ts.date()
    week_index_map: dict[pd.Period, int] = {}
    for idx, period_key in enumerate(weekly_periods, start=1):
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="W-SUN")
        week_index_map[period] = idx
    recurring_entries = _build_recurring_entries(frame, reference_date=recurring_ref_date)

    expenses = frame[(frame["amount"] < 0) & (~frame["is_refund"])].copy()
    # Actuals still respect the selected window; forecasts fill in remaining month weeks
    expenses = expenses[(expenses["date"] >= start_ts) & (expenses["date"] <= end_ts)]

    latest_observed_date = expenses["date"].max() if not expenses.empty else None
    observed_cutoff_period = latest_observed_date.to_period("W-SUN") if latest_observed_date is not None else None
    observed_cutoff_date = latest_observed_date.normalize() if latest_observed_date is not None else None

    expenses["week"] = expenses["date"].dt.to_period("W-SUN")
    actual_totals = expenses.groupby("week")["amount"].sum().abs()

    history_records = _weekly_history(frame, start_ts=start_ts)

    actual_records: list[WeeklyHistoryRecord] = []
    month_counters: dict[tuple[int, int], int] = {}
    actual_totals_map = {}
    for period_key, value in actual_totals.sort_index().items():
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="W-SUN")
        actual_totals_map[period] = float(value)
        if observed_cutoff_period is not None and period > observed_cutoff_period:
            continue
        start = period.start_time
        month_key = (start.year, start.month)
        month_counters[month_key] = month_counters.get(month_key, 0) + 1
        week_idx = week_index_map.get(period, month_counters[month_key])
        actual_records.append(
            WeeklyHistoryRecord(
                week_of_month=week_idx,
                month=start.strftime("%B"),
                year=start.year,
                start_date=start.date().isoformat(),
                end_date=period.end_time.date().isoformat(),
                amount=float(value),
            )
        )

    forecast_requests = _upcoming_week_requests(
        periods=tuple(weekly_periods),
        observed_cutoff=observed_cutoff_period,
        recurring_entries=recurring_entries,
        week_index_map=week_index_map,
    )

    forecast_results_map: dict[int, WeeklyForecastResult] = {}
    if forecast_requests:
        forecast_results = forecast_weekly_spend(
            history=history_records,
            actuals=actual_records,
            upcoming=forecast_requests,
            api_key=api_key,
        )
        forecast_results_map = {result.week_of_month: result for result in forecast_results}

    points: list[WeeklySpendPoint] = []
    forecast_count = 0
    actual_count = 0
    month_counters.clear()
    for period_key in weekly_periods:
        period = period_key if isinstance(period_key, pd.Period) else pd.Period(str(period_key), freq="W-SUN")
        start = period.start_time
        month_key = (start.year, start.month)
        month_counters[month_key] = month_counters.get(month_key, 0) + 1
        week_idx = week_index_map.get(period, month_counters[month_key])
        week_label = _format_week_label(period)

        week_complete = (
            observed_cutoff_date is not None and period.end_time.normalize() <= observed_cutoff_date
        )
        if week_complete:
            amount = float(actual_totals_map.get(period, 0.0))
            actual_count += 1
            points.append(WeeklySpendPoint(week_label=week_label, amount=amount, is_forecast=False))
        else:
            forecast = forecast_results_map.get(week_idx)
            amount = float(forecast.amount if forecast is not None else 0.0)
            confidence = float(forecast.confidence if forecast is not None else 0.0)
            forecast_count += 1
            points.append(
                WeeklySpendPoint(
                    week_label=week_label,
                    amount=amount,
                    is_forecast=True,
                    confidence=confidence,
                )
            )

    subtitle_parts = []
    if actual_count:
        subtitle_parts.append(f"{actual_count} actual")
    if forecast_count:
        subtitle_parts.append(f"{forecast_count} AI forecast")
    subtitle = " · ".join(subtitle_parts) if subtitle_parts else "No data"

    return WeeklySpendSeries(
        title="Spend by week",
        subtitle=subtitle,
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


# Number of days before a recurring charge when we flag it as "Due soon".
# Adjust as needed if you want a wider or narrower window.
DUE_SOON_THRESHOLD_DAYS = 5


def _status_from_days(days_until_due: int) -> str:
    if days_until_due < 0:
        return "Overdue"
    if days_until_due <= DUE_SOON_THRESHOLD_DAYS:
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
    # Slightly relax thresholds so more recurring items qualify
    return detect_recurring_transactions(
        expenses,
        today=today,
        amount_tolerance=0.15,
        min_occurrences=2,
    )


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
    top_n: int = 8,
) -> RecurringChargesTracker:
    entries = _build_recurring_entries(transactions, reference_date=reference_date)
    if not entries:
        return RecurringChargesTracker("Recurring charges", "Upcoming", ())

    # Restrict to monthly bills only (utilities, rent) and exclude subscriptions/fitness/etc.
    allowed_categories = {"utilities", "rent"}
    monthly_bills = [
        e for e in entries
        if int(e.get("interval_days", 0)) >= 28
        and str(e.get("category", "")).lower() in allowed_categories
    ]

    sorted_entries = sorted(
        monthly_bills,
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
    subscriptions: SubscriptionTracker,
    recurring: RecurringChargesTracker,
) -> AISummary:
    def _budget_payload(b: BudgetTracker) -> Mapping[str, object]:
        return {
            "title": b.title,
            "current_spend": b.current_spend,
            "projected_or_actual_spend": b.projected_or_actual_spend,
            "savings_projection": b.savings_projection,
            "variance_percent": b.variance_percent,
            "allocated_budget": b.allocated_budget,
            "is_under_budget": b.is_under_budget,
            "is_month_complete": b.is_month_complete,
        }

    def _snapshot_metrics_payload(snap: MonthlySnapshot) -> list[Mapping[str, object]]:
        return [
            {
                "label": metric.label,
                "value": metric.value,
                "delta": metric.delta,
                "is_positive": metric.is_positive,
            }
            for metric in snap.metrics
        ]

    def _categories_payload(summary: CategorySummary) -> list[Mapping[str, object]]:
        categories_payload: list[Mapping[str, object]] = []
        for category in summary.categories:
            categories_payload.append(
                {
                    "name": category.name,
                    "amount": category.amount,
                    "share": category.share,
                    "previous_amount": category.previous_amount,
                    "change_amount": category.change_amount,
                    "change_pct": category.change_pct,
                    "merchants": [
                        {
                            "name": merchant.name,
                            "amount": merchant.amount,
                            "share": merchant.share,
                        }
                        for merchant in category.merchants
                    ],
                }
            )
        return categories_payload

    def _subscriptions_payload(tracker: SubscriptionTracker) -> Mapping[str, object]:
        return {
            "title": tracker.title,
            "subtitle": tracker.subtitle,
            "total_monthly": tracker.total_monthly,
            "total_cumulative": tracker.total_cumulative,
            "items": [
                {
                    "name": subscription.name,
                    "monthly_cost": subscription.monthly_cost,
                    "months_active": subscription.months_active,
                    "cumulative_cost": subscription.cumulative_cost,
                }
                for subscription in tracker.subscriptions
            ],
        }

    def _recurring_payload(tracker: RecurringChargesTracker) -> Mapping[str, object]:
        return {
            "title": tracker.title,
            "subtitle": tracker.subtitle,
            "items": [
                {
                    "name": charge.name,
                    "amount": charge.amount,
                    "cadence": charge.cadence,
                    "next_date": charge.next_date,
                    "status": charge.status,
                }
                for charge in tracker.charges
            ],
        }

    focus_options = tuple(definition.label for definition in SUMMARY_FOCUS_DEFINITIONS)

    analytics_context: Mapping[str, object] = {
        "timeframe": {
            "start_date": category_summary.start_date.isoformat(),
            "end_date": category_summary.end_date.isoformat(),
        },
        "snapshot": {
            "title": snapshot.title,
            "period_label": snapshot.period_label,
        },
        "snapshot_metrics": _snapshot_metrics_payload(snapshot),
        "budget": _budget_payload(budget),
        "categories": _categories_payload(category_summary),
        "subscriptions": _subscriptions_payload(subscriptions),
        "recurring": _recurring_payload(recurring),
    }

    focus_output = build_focus_summaries(analytics_context=analytics_context)

    focus_map: dict[str, AISummaryFocus] = {}
    for option in focus_options:
        data = focus_output.get(option, {})
        headline = str(data.get("headline", "No insight available"))
        narrative = str(data.get("narrative", ""))
        bullets_raw = data.get("bullets")
        if isinstance(bullets_raw, Sequence) and not isinstance(bullets_raw, (str, bytes)):
            bullets = tuple(str(item) for item in bullets_raw if str(item).strip())
        else:
            bullets = ()
        if not bullets:
            bullets = ("Not enough data to generate guidance yet.",)
        focus_map[option] = AISummaryFocus(
            headline=headline,
            narrative=narrative or "Insights will appear here soon.",
            supporting_points=bullets,
        )

    return AISummary(
        focus_options=focus_options,
        default_focus=focus_options[0],
        focus_summaries=focus_map,
    )


def build_dashboard_context(
    transactions: pd.DataFrame,
    *,
    start_date: date,
    end_date: date,
    api_key: str | None = None,
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

    subscriptions = build_subscription_tracker(
        frame,
        start_date=start_date,
        end_date=end_date,
        reference_date=end_date,
    )
    recurring = build_recurring_charges_tracker(frame, reference_date=end_date)
    ai_summary = generate_ai_summary(
        snapshot=snapshot,
        budget=budget,
        category_summary=category_summary,
        subscriptions=subscriptions,
        recurring=recurring,
    )
    weekly_spend = build_weekly_spend_series(
        frame,
        start_date=start_date,
        end_date=end_date,
        api_key=api_key,
    )
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
