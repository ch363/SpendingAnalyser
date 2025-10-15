"""Yearly net flow chart component (single card_html render)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from core.models import MonthlyFlow, NetFlowSeries


# ---- lightweight card CSS (scoped inside iframe) ----
_CARD_CSS = """
<style>
.app-card{background:#fff;border-radius:1.25rem;padding:1.5rem;border:1px solid rgba(148,163,184,.16);
  box-shadow:0 18px 36px rgba(15,23,42,.08)}
.app-card__header{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem}
.pill{display:inline-flex;align-items:center;padding:.35rem .8rem;border-radius:999px;
  background:rgba(37,99,235,.10);font-size:.72rem;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:#2563eb}
.app-card__title{margin:.35rem 0 0;font-size:1.25rem;font-weight:600;color:#0f172a}
.chart-wrap{margin-top:1rem}
.muted{color:rgba(15,23,42,.6)}
</style>
"""


def _card_html(series: NetFlowSeries, chart_html: str) -> str:
    return _CARD_CSS + f"""
<div class="app-card" role="region" aria-label="Yearly net flow">
  <div class="app-card__header">
    <div>
      <div class="pill">{series.subtitle}</div>
      <h3 class="app-card__title">{series.title}</h3>
    </div>
  </div>

  <div class="chart-wrap">
    {chart_html}
  </div>
</div>
"""


def render_yearly_net_flow(series: NetFlowSeries) -> None:
    """Render grouped bar chart of monthly inflow/outflow inside a single card_html iframe."""
    # Filter out months with no inflow/outflow
    months_with_data = [m for m in series.months if (m.inflow != 0 or m.outflow != 0)]

    # Empty state
    if not months_with_data:
        empty_card = _CARD_CSS + f"""
        <div class="app-card">
          <div class="app-card__header">
            <div>
              <div class="pill">{series.subtitle}</div>
              <h3 class="app-card__title">{series.title}</h3>
            </div>
          </div>
          <p class="muted" style="margin-top:.75rem;">No monthly net flow data available.</p>
        </div>
        """
        components.html(empty_card, height=180, scrolling=False)
        return

    # Build dataframe only for months that have data
    df = pd.DataFrame(
        {
            "Month": [m.month for m in months_with_data for _ in (0, 1)],
            "Type": [label for _ in months_with_data for label in ("In", "Out")],
            "Amount": [value for m in months_with_data for value in (m.inflow, -m.outflow)],
        }
    )
    df["Display"] = df["Amount"].abs()

    # Map months to numeric positions so Plotly won't reserve space for missing months
    month_order = [m.month for m in months_with_data]
    month_to_idx = {m: i for i, m in enumerate(month_order)}
    df["MonthIdx"] = df["Month"].map(month_to_idx)

    # Figure
    fig = px.bar(
        df,
        x="MonthIdx",
        y="Display",
        color="Type",
        barmode="group",
        color_discrete_map={"In": "#00ff6a", "Out": "#ff0000"},
        text="Display",
    )
    fig.update_traces(
        texttemplate="£%{text:,.0f}",
        hovertemplate="%{customdata[0]} · %{customdata[1]}<br>£%{y:,.0f}<extra></extra>",
        customdata=df[["Type", "Month"]].to_numpy(),
        cliponaxis=False,
    )
    fig.update_layout(
        margin=dict(l=70, r=10, t=10, b=40),
        yaxis_title="",
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(showgrid=True, gridcolor="rgba(11,26,51,0.08)", zerolinecolor="rgba(11,26,51,0.2)"),
    )
    fig.update_yaxes(tickformat="£,.0f", tickfont=dict(color="rgba(15,23,42,0.85)", size=12))
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(month_to_idx.values()),
        ticktext=month_order,
        tickfont=dict(size=12),
        showgrid=False,
    )

    # Inline the chart so a single iframe render contains everything
    chart_html = fig.to_html(full_html=False, include_plotlyjs="inline", config={"displayModeBar": False})

    # Build and render the card in one go
    card_html = _card_html(series, chart_html)
    
    components.html(card_html, height=550, scrolling=False)


__all__ = ["MonthlyFlow", "NetFlowSeries", "render_yearly_net_flow"]
