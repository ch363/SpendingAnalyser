"""Category insight component — all content inside one white card."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import textwrap

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


def _format_currency(amount: float) -> str: return f"£{amount:,.0f}"
def _format_percent(ratio: float) -> str: return f"{ratio * 100:.1f}%"
def _format_change(amount: float) -> str:
    if amount == 0: return "£0"
    sign = "+" if amount > 0 else "-"
    return f"{sign}£{abs(amount):,.0f}"
def _format_change_pct(ratio: float) -> str:
    sign = "+" if ratio > 0 else ""
    return f"{sign}{ratio * 100:.1f}%"

def _status_badge(change_ratio: float) -> tuple[str, str]:
    if change_ratio < 0: return "Improved", "status-badge status-badge--improved"
    if change_ratio > 0: return "Higher", "status-badge status-badge--higher"
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
    return pd.DataFrame({
        "Category": [c.name for c in categories],
        "CurrentValue": [c.amount for c in categories],
        "Share": [c.share for c in categories],
        "ChangeAmount": [getattr(c, "change_amount", 0.0) for c in categories],
        "PctChange": [getattr(c, "change_pct", 0.0) for c in categories],
    })

def _vendor_dataframe(merchants: Iterable[MerchantSpend]) -> pd.DataFrame:
    return pd.DataFrame({
        "label": [m.name for m in merchants],
        "amount": [m.amount for m in merchants],
        "share": [m.share for m in merchants],
    })

def _inject_card_styles():
    css = """
    <style>
    /* style the VerticalBlock that *contains* our sentinel */
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="element-container"] .category-card__sentinel) {
        background: #ffffff;
        border-radius: 1.75rem;
        padding: 2rem;
        box-shadow: 0 25px 45px rgba(15, 23, 42, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.16);
    }
    .category-card__header { display:flex; justify-content:space-between; align-items:flex-start; gap:1.5rem; }
    .category-card__intro h2 { margin: .65rem 0 .35rem; font-size: 1.9rem; font-weight: 600; color:#0f172a; }
    .category-card__total { font-size: .95rem; color: rgba(15,23,42,.6); }
    .category-card__pill {
        display:inline-flex; align-items:center; padding:.4rem .9rem; border-radius:999px;
        background: rgba(37,99,235,.1); font-size:.75rem; font-weight:600; letter-spacing:.08em;
        text-transform:uppercase; color:#2563eb;
    }
    .status-badge {
        display:inline-flex; align-items:center; justify-content:center; height:36px; padding:0 1.1rem;
        border-radius:999px; font-size:.8rem; font-weight:600; background:rgba(148,163,184,.16);
        color:rgba(15,23,42,.68); text-transform:uppercase; letter-spacing:.06em;
    }
    .status-badge--improved { background: rgba(34,197,94,.16); color:#15803d; }
    .status-badge--higher   { background: rgba(239,68,68,.16);  color:#b91c1c; }
    .status-badge--neutral  { background: rgba(148,163,184,.16); color:rgba(15,23,42,.68); }

    .category-card__metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
        gap:1.1rem; margin-top:1.6rem; }
    .category-card__metric { padding:1rem 1.2rem; border-radius:1rem; background:rgba(241,245,249,.6);
        display:flex; flex-direction:column; gap:.35rem; }
    .category-card__metric span:first-child { font-size:.8rem; font-weight:600; text-transform:uppercase;
        letter-spacing:.08em; color:rgba(15,23,42,.55); }
    .category-card__metric strong { font-size:1.25rem; color:#0f172a; }

    .category-card__top-merchant { margin-top:1.4rem; }
    .category-card__top-merchant span { font-size:.85rem; font-weight:600; color:rgba(15,23,42,.65);
        text-transform:uppercase; letter-spacing:.08em; }
    .category-card__top-merchant p { margin:.5rem 0 0; font-size:.95rem; color:rgba(15,23,42,.85); }
    </style>
    """
    st.markdown(textwrap.dedent(css), unsafe_allow_html=True)

def render_category_breakdown(summary: CategorySummary) -> None:
    """Render the category insight card; everything lives inside ONE container."""

    # Empty state (still inside a card)
    if not summary.categories:
        _inject_card_styles()
        with st.container():
            st.markdown("<div class='category-card__sentinel'></div>", unsafe_allow_html=True)
            st.markdown(textwrap.dedent("""
            <div class='category-card__empty'>
                <div class='category-card__pill'>Where money went</div>
                <h3 style="margin:.8rem 0 .4rem;font-size:1.5rem;font-weight:600;color:#0f172a;">No spend recorded</h3>
                <p style="margin:0;font-size:.95rem;color:rgba(15,23,42,.6);">Select another period to review category spend.</p>
            </div>
            """), unsafe_allow_html=True)
        return

    # Normal state — EVERYTHING stays inside this single container
    _inject_card_styles()
    categories = list(summary.categories)
    category_df = _category_dataframe(categories)

    with st.container():
        # Sentinel marks this block as the card root
        st.markdown("<div class='category-card__sentinel'></div>", unsafe_allow_html=True)

        header_cols = st.columns([1.25, 0.75])
        with header_cols[0]:
            st.markdown(textwrap.dedent(f"""
            <div class='category-card__header'>
              <div class='category-card__intro'>
                <div class='category-card__pill'>Where money went</div>
                <h2>Category insight</h2>
                <span class='category-card__total'>{_format_currency(summary.total_amount)} total</span>
              </div>
            </div>
            """), unsafe_allow_html=True)

        with header_cols[1]:
            selected_name = st.selectbox(
                "Category",
                category_df["Category"],
                index=0,
                key="category_insight_selector",
            )

        # Compute selection + charts INSIDE the same container
        selected = next(c for c in categories if c.name == selected_name)
        metrics = _format_metrics(selected)
        vendor_df = _vendor_dataframe(selected.merchants)

        chart = build_category_chart(category_df)
        vendor_chart = build_vendor_chart(vendor_df)

        top_merchant = selected.merchants[0] if selected.merchants else None
        top_merchant_html = (
            f"<strong>{top_merchant.name}</strong> · {_format_percent(top_merchant.share)} of category"
            if top_merchant else "No merchant insights yet"
        )

        chart_col, detail_col = st.columns([1.05, 0.95], gap="large")

        with chart_col:
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})

        with detail_col:
            st.markdown(textwrap.dedent(f"""
            <div class='category-detail-panel category-card__metrics-wrapper'>
              <div class='category-detail-panel__header' style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                <div>
                  <h4 style="margin:0 0 .25rem 0;">{selected.name}</h4>
                  <span class='category-detail-panel__range'>
                    Showing spend for {summary.start_date.strftime('%d %b %Y')} – {summary.end_date.strftime('%d %b %Y')}
                  </span>
                </div>
                <span class='{metrics.badge_class}'>{metrics.badge_label}</span>
              </div>

              <div class='category-card__metrics'>
                <div class='category-card__metric'><span>This period</span><strong>{metrics.this_period}</strong></div>
                <div class='category-card__metric'><span>Share</span><strong>{metrics.share}</strong></div>
                <div class='category-card__metric'><span>Previous</span><strong>{metrics.previous}</strong></div>
                <div class='category-card__metric'><span>Change</span><strong>{metrics.change_amount}</strong><small>{metrics.change_pct}</small></div>
              </div>

              <div class='category-card__top-merchant'>
                <span>Top merchants this month</span>
                <p>{top_merchant_html}</p>
              </div>
            </div>
            """), unsafe_allow_html=True)

            st.plotly_chart(vendor_chart, use_container_width=True, config={"displayModeBar": False})
            st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)


__all__ = ["render_category_breakdown"]
