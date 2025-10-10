"""Sample data payloads for the Streamlit scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.components.ai_summary import AISummary
from app.components.budget_tracker import BudgetTracker
from app.components.category_breakdown import CategoryBreakdown, CategorySlice
from app.components.monthly_snapshot import MonthlySnapshot, SnapshotMetric
from app.components.net_flow import MonthlyFlow, NetFlowSeries
from app.components.recurring_charges import RecurringCharge, RecurringChargesTracker
from app.components.subscriptions import Subscription, SubscriptionTracker
from app.components.weekly_spend import WeeklySpendPoint, WeeklySpendSeries


@dataclass(frozen=True)
class DashboardSample:
    ai_summary: AISummary
    monthly_snapshot: MonthlySnapshot
    budget_tracker: BudgetTracker
    category_breakdown: CategoryBreakdown
    subscriptions: SubscriptionTracker
    weekly_spend: WeeklySpendSeries
    recurring_charges: RecurringChargesTracker
    net_flow: NetFlowSeries
    default_date_range: tuple[date, date]


def load_demo_dashboard() -> DashboardSample:
    """Return a coherent set of demo values for the dashboard scaffold."""

    ai_summary = AISummary(
        headline="Spending is trending 12% under plan thanks to lower dining costs.",
        supporting_points=(
            "Redirect the remaining £320 from dining into your ISA to stay on pace.",
            "Transport costs have stabilised; expect a £140 reduction versus last month.",
            "Watch subscriptions — Disney+ annual renewal lands in two weeks (£89).",
        ),
        focus_options=("Staying under budget", "Grow savings", "Cut discretionary"),
        default_focus="Staying under budget",
    )

    snapshot = MonthlySnapshot(
        title="October pulse",
        period_label="Month to date",
        metrics=(
            SnapshotMetric(
                label="Total spend",
                value="£2,480",
                delta="-£340 vs last month",
                is_positive=True,
            ),
            SnapshotMetric(
                label="Change",
                value="-12%",
                delta="Better than typical",
                is_positive=True,
            ),
            SnapshotMetric(
                label="Lowest day",
                value="£42 (12 Oct)",
            ),
            SnapshotMetric(
                label="Highest day",
                value="£310 (04 Oct)",
            ),
            SnapshotMetric(
                label="Projected savings",
                value="£890",
                delta="If current trend holds",
                is_positive=True,
            ),
            SnapshotMetric(
                label="Cashback earned",
                value="£32",
                delta="New highs",
                is_positive=True,
            ),
        ),
    )

    tracker = BudgetTracker(
        title="Budget tracking",
        current_spend=2480,
        projected_or_actual_spend=3050,
        savings_projection=3200 - 3050,
        variance_percent=4.7,
        allocated_budget=3200,
        is_under_budget=True,
        is_month_complete=False,
    )

    category_breakdown = CategoryBreakdown(
        title="Category split",
        subtitle="Spending mix",
        slices=(
            CategorySlice(name="Housing", value=1180, share=34, change=2.0, is_positive=False),
            CategorySlice(name="Transport", value=240, share=7, change=-6.1, is_positive=True),
            CategorySlice(name="Groceries", value=486, share=14, change=1.5, is_positive=False),
            CategorySlice(name="Dining out", value=210, share=6, change=-11.2, is_positive=True),
            CategorySlice(name="Subscriptions", value=195, share=6, change=8.5, is_positive=False),
            CategorySlice(name="Investments", value=169, share=5, change=4.4, is_positive=True),
        ),
    )

    subscription_items = (
        Subscription(name="Netflix", monthly_cost=12, months_active=28),
        Subscription(name="Spotify", monthly_cost=10, months_active=42),
        Subscription(name="Disney+", monthly_cost=8, months_active=11),
        Subscription(name="Prime", monthly_cost=9, months_active=36),
        Subscription(name="FT Weekend", monthly_cost=22, months_active=9),
    )
    subscriptions = SubscriptionTracker(
        title="Subscriptions tracker",
        subtitle="Recurring services",
        subscriptions=subscription_items,
        total_monthly=sum(sub.monthly_cost for sub in subscription_items),
        total_cumulative=sum(sub.cumulative_cost for sub in subscription_items),
    )

    weekly_spend = WeeklySpendSeries(
        title="Spend by week",
        subtitle="Last 6 weeks",
        points=(
            WeeklySpendPoint(week_label="Week 35", amount=620),
            WeeklySpendPoint(week_label="Week 36", amount=540),
            WeeklySpendPoint(week_label="Week 37", amount=480),
            WeeklySpendPoint(week_label="Week 38", amount=515),
            WeeklySpendPoint(week_label="Week 39", amount=460),
            WeeklySpendPoint(week_label="Week 40", amount=365),
        ),
    )

    recurring_charges = RecurringChargesTracker(
        title="Recurring charges",
        subtitle="Upcoming",
        charges=(
            RecurringCharge(name="Gym membership", cadence="Monthly", next_date="20 Oct", amount=45, status="Up to date"),
            RecurringCharge(name="Disney+ annual", cadence="Yearly", next_date="28 Oct", amount=89, status="Due soon"),
            RecurringCharge(name="Council tax", cadence="Monthly", next_date="01 Nov", amount=145, status="Up to date"),
            RecurringCharge(name="Car insurance", cadence="Annual", next_date="12 Dec", amount=420, status="Planned"),
        ),
    )

    net_flow = NetFlowSeries(
        title="Yearly net flow",
        subtitle="2025",
        months=(
            MonthlyFlow(month="Jan", inflow=4200, outflow=3850),
            MonthlyFlow(month="Feb", inflow=4150, outflow=4010),
            MonthlyFlow(month="Mar", inflow=4350, outflow=3980),
            MonthlyFlow(month="Apr", inflow=4400, outflow=4100),
            MonthlyFlow(month="May", inflow=4520, outflow=4225),
            MonthlyFlow(month="Jun", inflow=4475, outflow=4390),
            MonthlyFlow(month="Jul", inflow=4600, outflow=4450),
            MonthlyFlow(month="Aug", inflow=4550, outflow=4380),
            MonthlyFlow(month="Sep", inflow=4625, outflow=4310),
            MonthlyFlow(month="Oct", inflow=4680, outflow=4175),
            MonthlyFlow(month="Nov", inflow=4700, outflow=4290),
            MonthlyFlow(month="Dec", inflow=5200, outflow=4980),
        ),
    )

    default_range = (date(2025, 10, 1), date(2025, 10, 31))

    return DashboardSample(
        ai_summary=ai_summary,
        monthly_snapshot=snapshot,
        budget_tracker=tracker,
        category_breakdown=category_breakdown,
        subscriptions=subscriptions,
        weekly_spend=weekly_spend,
        recurring_charges=recurring_charges,
        net_flow=net_flow,
        default_date_range=default_range,
    )


__all__ = ["DashboardSample", "load_demo_dashboard"]
