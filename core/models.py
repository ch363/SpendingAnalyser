"""Core dataclasses for analytics summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping, Tuple


@dataclass(frozen=True)
class MerchantSpend:
    """Spend contribution from an individual merchant within a category."""

    name: str
    amount: float
    share: float  # expressed as decimal (0-1)


@dataclass(frozen=True)
class CategorySpend:
    """Aggregate spend metrics for a single spending category."""

    name: str
    amount: float
    share: float  # expressed as decimal (0-1)
    previous_amount: float
    change_amount: float
    change_pct: float  # expressed as decimal (e.g. -0.21 == -21%)
    merchants: Tuple[MerchantSpend, ...] = ()


@dataclass(frozen=True)
class CategorySummary:
    """Encapsulates the donut chart and detail card inputs."""

    title: str
    subtitle: str
    start_date: date
    end_date: date
    total_amount: float
    categories: Tuple[CategorySpend, ...]


@dataclass(frozen=True)
class SnapshotMetric:
    """Display-ready metric for the monthly snapshot card."""

    label: str
    value: str
    delta: str | None = None
    is_positive: bool | None = None


@dataclass(frozen=True)
class MonthlySnapshot:
    """Collection of snapshot metrics for a given period."""

    title: str
    period_label: str
    metrics: Tuple[SnapshotMetric, ...]
    # Optional baseline classification and explanation for the header badge
    baseline_label: str | None = None
    baseline_tooltip: str | None = None


@dataclass(frozen=True)
class BudgetTracker:
    """Budget overview inputs derived from transaction analytics."""

    title: str
    current_spend: float
    projected_or_actual_spend: float
    savings_projection: float
    variance_percent: float
    allocated_budget: float
    is_under_budget: bool
    is_month_complete: bool


@dataclass(frozen=True)
class AISummaryFocus:
    """Renderable content for a specific AI summary focus option."""

    headline: str
    narrative: str
    supporting_points: Tuple[str, ...]


@dataclass(frozen=True)
class AISummary:
    """Structured copy used by the AI hero card."""

    focus_options: Tuple[str, ...]
    default_focus: str
    focus_summaries: Mapping[str, AISummaryFocus]


@dataclass(frozen=True)
class WeeklySpendPoint:
    week_label: str
    amount: float
    is_forecast: bool = False
    confidence: float | None = None


@dataclass(frozen=True)
class WeeklySpendSeries:
    title: str
    subtitle: str
    points: Tuple[WeeklySpendPoint, ...]


@dataclass(frozen=True)
class Subscription:
    name: str
    monthly_cost: float
    months_active: int

    @property
    def cumulative_cost(self) -> float:
        return self.monthly_cost * self.months_active


@dataclass(frozen=True)
class SubscriptionTracker:
    title: str
    subtitle: str
    subscriptions: Tuple[Subscription, ...]
    total_monthly: float
    total_cumulative: float


@dataclass(frozen=True)
class RecurringCharge:
    name: str
    amount: float
    cadence: str
    next_date: str
    status: str


@dataclass(frozen=True)
class RecurringChargesTracker:
    title: str
    subtitle: str
    charges: Tuple[RecurringCharge, ...]


@dataclass(frozen=True)
class MonthlyFlow:
    month: str
    inflow: float
    outflow: float


@dataclass(frozen=True)
class NetFlowSeries:
    title: str
    subtitle: str
    months: Tuple[MonthlyFlow, ...]


@dataclass(frozen=True)
class ProgressRow:
    """Helper model for category progress visualisations."""

    category: str
    label: str
    delta: str
    width: int


@dataclass(frozen=True)
class VendorRow:
    """Helper model for vendor share tables."""

    category: str
    label: str
    amount: float
    share: float


__all__ = [
    "MerchantSpend",
    "CategorySpend",
    "CategorySummary",
    "SnapshotMetric",
    "MonthlySnapshot",
    "BudgetTracker",
    "AISummaryFocus",
    "AISummary",
    "WeeklySpendPoint",
    "WeeklySpendSeries",
    "Subscription",
    "SubscriptionTracker",
    "RecurringCharge",
    "RecurringChargesTracker",
    "MonthlyFlow",
    "NetFlowSeries",
    "ProgressRow",
    "VendorRow",
]
