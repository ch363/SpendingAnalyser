"""UI component primitives for the Streamlit dashboard scaffold."""

from core.models import (
    BudgetTracker,
    NetFlowSeries,
    RecurringCharge,
    RecurringChargesTracker,
    Subscription,
    SubscriptionTracker,
    WeeklySpendPoint,
    WeeklySpendSeries,
)

from .ai_summary import render_ai_summary_card
from .budget_tracker import render_budget_spend_insights
from .category_breakdown import render_category_breakdown
from .monthly_snapshot import render_snapshot_card
from .net_flow import render_yearly_net_flow
from .recurring_charges import render_recurring_charges
from .subscriptions import render_subscriptions
from .weekly_spend import render_weekly_spend

__all__ = [
    "render_ai_summary_card",
    "render_snapshot_card",
    "render_budget_spend_insights",
    "render_category_breakdown",
    "render_subscriptions",
    "render_weekly_spend",
    "render_recurring_charges",
    "render_yearly_net_flow",
    "BudgetTracker",
    "Subscription",
    "SubscriptionTracker",
    "WeeklySpendPoint",
    "WeeklySpendSeries",
    "RecurringCharge",
    "RecurringChargesTracker",
    "NetFlowSeries",
]
