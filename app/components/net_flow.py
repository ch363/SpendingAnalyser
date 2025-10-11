"""Yearly net flow chart component."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

from core.models import MonthlyFlow, NetFlowSeries


def render_yearly_net_flow(series: NetFlowSeries) -> None:
    """Render grouped bar chart of monthly inflow/outflow."""
    # Filter out months with no inflow and no outflow so they don't appear.
    months_with_data = [m for m in series.months if (m.inflow != 0 or m.outflow != 0)]

    # If there's no data at all, render an empty card message and return.
    if not months_with_data:
        empty_html = f"""
        <div class='app-card netflow-card'>
          <div class="app-card__header">
            <div>
              <div class="pill">{series.subtitle}</div>
              <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{series.title}</h3>
            </div>
          </div>
          <div style='padding:1.25rem; color: var(--app-text-muted);'>No monthly net flow data available.</div>
        </div>
        """
        components.html(empty_html, height=140, scrolling=False)
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

    # Map months to numeric positions so Plotly won't reserve space for missing months.
    month_order = [m.month for m in months_with_data]
    month_to_idx = {m: i for i, m in enumerate(month_order)}
    df["MonthIdx"] = df["Month"].map(month_to_idx)

    fig = px.bar(
        df,
        x="MonthIdx",
        y="Display",
        color="Type",
        barmode="group",
        color_discrete_map={"In": "#00ff48", "Out": "#ff0000"},
        text="Display",
    )
    fig.update_traces(
        texttemplate="£%{text:,.0f}",
        hovertemplate="%{x} %{customdata[0]}: £%{customdata[1]:,.0f}<extra></extra>",
        customdata=df[["Type", "Display"]].values,
    )

    # Increase left margin so y-axis labels are visible and style axis ticks
    fig.update_layout(
        margin=dict(l=80, r=10, t=10, b=30),
        yaxis_title="",
        xaxis_title="",
        legend=dict(orientation="h", y=-0.2, x=0.2),
        yaxis=dict(showgrid=True, gridcolor="rgba(11, 26, 51, 0.08)", zerolinecolor="rgba(11,26,51,0.2)", tickfont=dict(size=12, color="rgba(11,26,51,0.8)")),
    )

    # Format y-axis as pounds and ensure ticks are readable
    fig.update_yaxes(tickformat="£,.0f", tickfont=dict(color="rgba(11,26,51,0.85)", size=13), showticklabels=True)

    # Show only the months present by placing ticks at the numeric positions
    # and labelling them with the month names.
    fig.update_xaxes(tickmode="array", tickvals=list(month_to_idx.values()), ticktext=month_order, tickfont=dict(size=12))

    # Render header and figure HTML together inside a single Streamlit components.html call
    plot_html = pio.to_html(fig, include_plotlyjs=True, full_html=False)
    card_html = f"""
    <div class='app-card netflow-card'>
      <div class="app-card__header">
        <div>
          <div class="pill">{series.subtitle}</div>
          <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{series.title}</h3>
        </div>
      </div>
      {plot_html}
    </div>
    """

    # Estimate height from figure layout; fallback to 420px.
    est_height = int(fig.layout.height) if fig.layout.height is not None else 420
    components.html(card_html, height=est_height, scrolling=False)


__all__ = ["MonthlyFlow", "NetFlowSeries", "render_yearly_net_flow"]
