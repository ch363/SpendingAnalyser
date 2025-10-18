"""Weekly spend chart component (single card_html render)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components

from core.models import WeeklySpendPoint, WeeklySpendSeries
from app.theme import FONT_STACK


# ---- lightweight card CSS (scoped inside the iframe) ----
_CARD_CSS = f"""
<style>
:root, html, body {{
  font-family: {FONT_STACK};
}}
body {{
  margin: 0;
  color: #0f172a;
  background: transparent;
}}
.app-card, .app-card * {{
  font-family: inherit;
}}
.app-card {{background:#fff;border-radius:1.25rem;padding:1.5rem;border:1px solid rgba(148,163,184,.16);
  box-shadow:0 18px 36px rgba(15,23,42,.08);}}
.app-card__header {{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;}}
.pill {{display:inline-flex;align-items:center;padding:.35rem .8rem;border-radius:999px;
  background:rgba(37,99,235,.10);font-size:.72rem;font-weight:600;letter-spacing:.06em;
  text-transform:uppercase;color:#2563eb;}}
.app-card__title {{margin:.35rem 0 0;font-size:1.25rem;font-weight:600;color:#0f172a;}}
.chart-wrap {{margin-top:1rem;}}
</style>
"""


def _card_html(series: WeeklySpendSeries, chart_html: str) -> str:
    return _CARD_CSS + f"""
<div class="app-card" role="region" aria-label="Weekly spend">
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


def render_weekly_spend(series: WeeklySpendSeries) -> None:
    """Render spend-by-week as a bar chart inside a single iframe."""

    if not series.points:
        empty_card = _CARD_CSS + """
        <div class="app-card">
          <div class="app-card__header">
            <div>
              <div class="pill">Weekly spend</div>
              <h3 class="app-card__title">No data</h3>
            </div>
          </div>
          <p style="margin:.5rem 0 0;color:rgba(15,23,42,.65);">
            There are no weekly spend points to show.
          </p>
        </div>
        """
        components.html(empty_card, height=220, scrolling=False)
        return

    dataframe = pd.DataFrame(
        {
            "Week": [point.week_label for point in series.points],
            "Spend": [point.amount for point in series.points],
            "Type": ["AI Forecast" if point.is_forecast else "Actual" for point in series.points],
            "Confidence": [point.confidence for point in series.points],
        }
    )

    color_map = {
        "Actual": "#3c79ff",
        "AI Forecast": "rgba(60, 121, 255, 0.28)",
    }

    fig = px.bar(
        dataframe,
        x="Week",
        y="Spend",
        text="Spend",
        color="Type",
        color_discrete_map=color_map,
    )
    fig.update_traces(
        texttemplate="£%{text:,.0f}",
        textposition="outside",
        hovertemplate="%{x} (%{customdata[0]}): £%{y:,.0f}<br>Confidence: %{customdata[1]:.0%}<extra></extra>",
        customdata=dataframe[["Type", "Confidence"]].fillna(0.0).to_numpy(),
        cliponaxis=False,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=30),
        yaxis_title="",
        xaxis_title="",
        yaxis=dict(showgrid=False, visible=False),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    chart_html = fig.to_html(full_html=False, include_plotlyjs="inline", config={"displayModeBar": False})
    components.html(_card_html(series, chart_html), height=590, scrolling=False)


__all__ = ["WeeklySpendPoint", "WeeklySpendSeries", "render_weekly_spend"]
