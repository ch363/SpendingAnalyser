"""Category insight component leveraging shared visualization builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import streamlit as st

from core.models import CategorySpend, CategorySummary, MerchantSpend
from visualization.charts import build_category_chart, build_vendor_chart


@dataclass(frozen=True)
class _FormattedMetrics:
    this_period: str
    share: str
    previous: str
    change_amount: str
    change_pct: str
    badge_label: str
    badge_class: str


def _format_currency(amount: float) -> str:
    return f"£{amount:,.0f}"


def _format_percent(ratio: float) -> str:
    return f"{ratio * 100:.1f}%"


def _format_change(amount: float) -> str:
    if amount == 0:
        return "£0"
    sign = "+" if amount > 0 else "-"
    return f"{sign}£{abs(amount):,.0f}"


def _format_change_pct(ratio: float) -> str:
    sign = "+" if ratio > 0 else ""
    return f"{sign}{ratio * 100:.1f}%"


def _status_badge(change_ratio: float) -> tuple[str, str]:
    if change_ratio < 0:
        return "Improved", "status-badge status-badge--improved"
    if change_ratio > 0:
        return "Higher", "status-badge status-badge--higher"
    return "Stable", "status-badge status-badge--neutral"


def _format_metrics(selected: CategorySpend) -> _FormattedMetrics:
    change_ratio = getattr(selected, "change_pct", 0.0)
    badge_label, badge_class = _status_badge(change_ratio)
    change_amount = getattr(selected, "change_amount", 0.0)
    return _FormattedMetrics(
        this_period=_format_currency(selected.amount),
        share=_format_percent(selected.share),
        previous=_format_currency(selected.previous_amount),
        change_amount=_format_change(change_amount),
        change_pct=_format_change_pct(change_ratio),
        badge_label=badge_label,
        badge_class=badge_class,
    )


def _category_dataframe(categories: Iterable[CategorySpend]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Category": [item.name for item in categories],
            "CurrentValue": [item.amount for item in categories],
            "Share": [item.share for item in categories],
            "ChangeAmount": [getattr(item, "change_amount", 0.0) for item in categories],
            "PctChange": [getattr(item, "change_pct", 0.0) for item in categories],
        }
    )


def _vendor_dataframe(merchants: Iterable[MerchantSpend]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "label": [merchant.name for merchant in merchants],
            "amount": [merchant.amount for merchant in merchants],
            "share": [merchant.share for merchant in merchants],
        }
    )


def render_category_breakdown(summary: CategorySummary) -> None:
    """Render the category insight card with shared visualization builders."""

    if not summary.categories:
        st.markdown(
            """
            <div class='category-insight category-insight--empty'>
                <div>
                    <div class='category-insight__pill'>Where money went</div>
                    <h3>No spend recorded</h3>
                    <p>Select another period to review category spend.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    categories = list(summary.categories)
    category_df = _category_dataframe(categories)

    st.markdown("<div class='category-insight'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='category-insight__surface'>
            <div class='category-insight__surface-inner'>
                <div class='category-insight__surface-body'>
        """,
        unsafe_allow_html=True,
    )

    header_cols = st.columns([1.2, 0.8])
    with header_cols[0]:
        st.markdown(
            f"""
            <div class='category-insight__intro'>
                <div class='category-insight__pill'>Where money went</div>
                <h2>Category insight</h2>
                <span class='category-insight__total'>{_format_currency(summary.total_amount)} total</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_cols[1]:
        selected_name = st.selectbox(
            "Category",
            category_df["Category"],
            index=0,
            key="category_insight_selector",
        )

    selected = next(item for item in categories if item.name == selected_name)
    metrics = _format_metrics(selected)

    vendor_df = _vendor_dataframe(selected.merchants)

    chart = build_category_chart(category_df)
    vendor_chart = build_vendor_chart(vendor_df)

    top_merchant = selected.merchants[0] if selected.merchants else None
    top_merchant_html = (
        f"<strong>{top_merchant.name}</strong> · {_format_percent(top_merchant.share)} of category"
        if top_merchant
        else "No merchant insights yet"
    )

    chart_col, detail_col = st.columns([1.05, 0.95], gap="large")
    with chart_col:
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})

    with detail_col:
        st.markdown(
            f"""
            <div class='category-detail-panel'>
                <div class='category-detail-panel__header'>
                    <div>
                        <h4>{selected.name}</h4>
                        <span class='category-detail-panel__range'>
                            Showing spend for {summary.start_date.strftime('%d %b %Y')} – {summary.end_date.strftime('%d %b %Y')}
                        </span>
                    </div>
                    <span class='{metrics.badge_class}'>{metrics.badge_label}</span>
                </div>
                <div class='category-detail-panel__metrics'>
                    <div class='metric-card'>
                        <span> This period </span>
                        <strong>{metrics.this_period}</strong>
                    </div>
                    <div class='metric-card'>
                        <span> Share </span>
                        <strong>{metrics.share}</strong>
                    </div>
                    <div class='metric-card'>
                        <span> Previous </span>
                        <strong>{metrics.previous}</strong>
                    </div>
                    <div class='metric-card metric-card--delta'>
                        <span> Change </span>
                        <strong>{metrics.change_amount}</strong>
                        <small>{metrics.change_pct}</small>
                    </div>
                </div>
                <div class='category-detail-panel__top-merchant'>
                    <span>Top merchants this month</span>
                    <p>{top_merchant_html}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.plotly_chart(vendor_chart, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        """
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


__all__ = ["render_category_breakdown"]
