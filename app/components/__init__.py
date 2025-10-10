"""UI component primitives for the Streamlit dashboard scaffold."""

from .ai_summary import render_ai_summary
from .budget_tracker import BudgetTracker, render_budget_tracker
from .category_breakdown import (
    CategoryBreakdown,
    CategorySlice,
    render_category_breakdown_chart,
    render_category_breakdown_details,
)
from .monthly_snapshot import render_monthly_snapshot
from .net_flow import NetFlowSeries, render_yearly_net_flow
from .recurring_charges import (
    RecurringCharge,
    RecurringChargesTracker,
    render_recurring_charges,
)
from .subscriptions import Subscription, SubscriptionTracker, render_subscriptions
from .weekly_spend import WeeklySpendPoint, WeeklySpendSeries, render_weekly_spend

__all__ = [
    "render_ai_summary",
    "render_monthly_snapshot",
    "render_budget_tracker",
    "render_category_breakdown_chart",
    "render_category_breakdown_details",
    "render_subscriptions",
    "render_weekly_spend",
    "render_recurring_charges",
    "render_yearly_net_flow",
    "CategoryBreakdown",
    "CategorySlice",
    "BudgetTracker",
    "Subscription",
    "SubscriptionTracker",
    "WeeklySpendPoint",
    "WeeklySpendSeries",
    "RecurringCharge",
    "RecurringChargesTracker",
    "NetFlowSeries",
]
