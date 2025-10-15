from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components  # for one-shot HTML render

from core.models import CategorySpend, CategorySummary, MerchantSpend
from visualization.charts import build_category_chart, build_vendor_chart

# ---------- formatting ----------
@dataclass(frozen=True)
class _FormattedMetrics:
    this_period: str; share: str; previous: str
    change_amount: str; change_pct: str
    badge_label: str; badge_class: str

def _format_currency(x: float) -> str: return f"£{x:,.0f}"
def _format_percent(r: float) -> str:   return f"{r*100:.1f}%"
def _format_change(a: float) -> str:    return ("+£" if a>0 else "-£" if a<0 else "£")+f"{abs(a):,.0f}"
def _format_change_pct(r: float) -> str:return (f"+{r*100:.1f}%" if r>0 else f"{r*100:.1f}%")

def _status_badge(r: float) -> tuple[str, str]:
    if r < 0:  return "Improved", "status-badge status-badge--improved"
    if r > 0:  return "Higher",   "status-badge status-badge--higher"
    return "Stable", "status-badge status-badge--neutral"

def _fmt_metrics(c: CategorySpend) -> _FormattedMetrics:
    badge, cls = _status_badge(getattr(c, "change_pct", 0.0))
    return _FormattedMetrics(
        this_period=_format_currency(c.amount),
        share=_format_percent(c.share),
        previous=_format_currency(c.previous_amount),
        change_amount=_format_change(getattr(c, "change_amount", 0.0)),
        change_pct=_format_change_pct(getattr(c, "change_pct", 0.0)),
        badge_label=badge, badge_class=cls,
    )

# ---------- css ----------
_CARD_CSS = """
<style>
.category-card{background:#fff;border-radius:1.75rem;padding:2rem;border:1px solid rgba(148,163,184,.16);
 box-shadow:0 25px 45px rgba(15,23,42,.08)}
.category-card__header{display:flex;justify-content:space-between;align-items:flex-start;gap:1.5rem}
.category-card__pill{display:inline-flex;align-items:center;padding:.4rem .9rem;border-radius:999px;
 background:rgba(37,99,235,.1);font-size:.75rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#2563eb}
.category-card__intro h2{margin:.65rem 0 .35rem;font-size:1.9rem;font-weight:600;color:#0f172a}
.category-card__total{font-size:.95rem;color:rgba(15,23,42,.6)}
.status-badge{display:inline-flex;align-items:center;justify-content:center;height:36px;padding:0 1.1rem;border-radius:999px;
 font-size:.8rem;font-weight:600;background:rgba(148,163,184,.16);color:rgba(15,23,42,.68);text-transform:uppercase;letter-spacing:.06em}
.status-badge--improved{background:rgba(34,197,94,.16);color:#15803d}
.status-badge--higher{background:rgba(239,68,68,.16);color:#b91c1c}
.status-badge--neutral{background:rgba(148,163,184,.16);color:rgba(15,23,42,.68)}
.category-card__metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1.1rem;margin-top:1.6rem}
.category-card__metric{padding:1rem 1.2rem;border-radius:1rem;background:rgba(241,245,249,.6);display:flex;flex-direction:column;gap:.35rem}
.category-card__metric span:first-child{font-size:.8rem;font-weight:600;text-transform:uppercase;letter-spacing:.08em;color:rgba(15,23,42,.55)}
.category-card__metric strong{font-size:1.25rem;color:#0f172a}
.category-card__top-merchant{margin-top:1.4rem}
.category-card__top-merchant span{font-size:.85rem;font-weight:600;color:rgba(15,23,42,.65);text-transform:uppercase;letter-spacing:.08em}
.category-card__top-merchant p{margin:.5rem 0 0;font-size:.95rem;color:rgba(15,23,42,.85)}
.chart-wrap{margin-top:1.6rem; min-height:360px; overflow:hidden}

/* side-by-side charts */
.charts-grid{display:grid; grid-template-columns: 1.2fr 1fr; gap:2rem; align-items:start;}
@media (max-width: 900px){ .charts-grid{grid-template-columns: 1fr;} }
</style>
"""

# ---------- card builder ----------
def _card_html(summary: CategorySummary, selected_name: str,
               metrics: _FormattedMetrics, top_html: str,
               cat_chart_html: str, vend_chart_html: str) -> str:
    return _CARD_CSS + f"""
<section class="category-card" role="region" aria-label="Category insight">
  <header class="category-card__header">
    <div class="category-card__intro">
      <div class="category-card__pill">Where money went</div>
      <h2>Category insight</h2>
      <span class="category-card__total">{_format_currency(summary.total_amount)} total</span>
    </div>
    <span class="{metrics.badge_class}">{metrics.badge_label}</span>
  </header>

  <div class="category-detail-panel__range" style="margin:.25rem 0 1rem;color:rgba(15,23,42,.6)">
    Showing spend for {summary.start_date.strftime("%d %b %Y")} – {summary.end_date.strftime("%d %b %Y")} · <strong>{selected_name}</strong>
  </div>

  <div class="category-card__metrics">
    <div class="category-card__metric"><span>This period</span><strong>{metrics.this_period}</strong></div>
    <div class="category-card__metric"><span>Share</span><strong>{metrics.share}</strong></div>
    <div class="category-card__metric"><span>Previous</span><strong>{metrics.previous}</strong></div>
    <div class="category-card__metric"><span>Change</span><strong>{metrics.change_amount}</strong><small>{metrics.change_pct}</small></div>
  </div>

  <div class="charts-grid">
    <div class="chart-wrap">
      {cat_chart_html}
    </div>
    <div class="chart-wrap">
    <div class="category-card__top-merchant">
    <span>Top merchants this month</span>
    <p>{top_html}</p>
    </div>
      {vend_chart_html}
    </div>
  </div>

  
</section>
"""

# ---------- main render ----------
def render_category_breakdown(summary: CategorySummary) -> str:
    """Selector above-right. One card_html render; donut + bars inside the card."""
    if not summary.categories:
        # still render a card so layout stays consistent
        empty_html = _CARD_CSS + """
        <section class="category-card">
          <div class="category-card__intro">
            <div class="category-card__pill">Where money went</div>
            <h2>No spend recorded</h2>
            <p style="margin:0;font-size:.95rem;color:rgba(15,23,42,.6)">Select another period to review category spend.</p>
          </div>
        </section>"""
        components.html(empty_html, height=300, scrolling=False)
        return ""

    categories = list(summary.categories)

    # Selector above the card (right)
    left, right = st.columns([1.25, 0.75])
    with right:
        selected_name = st.selectbox("Category", [c.name for c in categories], index=0, key="category_insight_selector")

    selected = next(c for c in categories if c.name == selected_name)
    metrics = _fmt_metrics(selected)
    top = selected.merchants[0] if selected.merchants else None
    top_html = (f"<strong>{top.name}</strong> · {_format_percent(top.share)} of category") if top else "No merchant insights yet"

    # Build dataframes (as before)
    category_df = pd.DataFrame({
        "Category": [c.name for c in categories],
        "CurrentValue": [c.amount for c in categories],
        "Share": [c.share for c in categories],
        "ChangeAmount": [getattr(c, "change_amount", 0.0) for c in categories],
        "PctChange": [getattr(c, "change_pct", 0.0) for c in categories],
    })
    vendor_df = pd.DataFrame({
        "label": [m.name for m in selected.merchants],
        "amount": [m.amount for m in selected.merchants],
        "share": [m.share for m in selected.merchants],
    })

    # Build figures (as before)
    cat_fig  = build_category_chart(category_df)  # donut/pie
    vend_fig = build_vendor_chart(vendor_df)      # bars

    # Convert to HTML and embed JS inline so it renders inside the card iframe
    cat_html = cat_fig.to_html(full_html=False, include_plotlyjs="inline", config={"displayModeBar": False})
    # Include Plotly.js inline for the vendor chart as well to avoid any race/availability issues
    vend_html = vend_fig.to_html(full_html=False, include_plotlyjs="inline", config={"displayModeBar": False})

    # One HTML blob for the entire card
    card_html = _card_html(summary, selected_name, metrics, top_html, cat_html, vend_html)

    # Render once (reduced height due to side-by-side layout)
    components.html(card_html, height=860, scrolling=False)

    return selected_name
