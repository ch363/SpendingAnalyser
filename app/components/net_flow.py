"""Yearly net flow chart component."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd
import plotly.express as px
import streamlit as st


@dataclass(frozen=True)
class MonthlyFlow:
    month: str
    inflow: float
    outflow: float


@dataclass(frozen=True)
class NetFlowSeries:
    title: str
    subtitle: str
    months: Sequence[MonthlyFlow]


def render_yearly_net_flow(series: NetFlowSeries) -> None:
    """Render grouped bar chart of monthly inflow/outflow."""

    df = pd.DataFrame(
        {
            "Month": [m.month for m in series.months for _ in (0, 1)],
            "Type": [label for _ in series.months for label in ("In", "Out")],
            "Amount": [value for m in series.months for value in (m.inflow, -m.outflow)],
        }
    )
    df["Display"] = df["Amount"].abs()

    fig = px.bar(
        df,
        x="Month",
        y="Amount",
        color="Type",
        barmode="group",
        color_discrete_map={"In": "#00c2ff", "Out": "#3c79ff"},
        text="Display",
    )
    fig.update_traces(
        texttemplate="£%{text:,.0f}",
        hovertemplate="%{x} %{customdata[0]}: £%{customdata[1]:,.0f}<extra></extra>",
        customdata=df[["Type", "Display"]].values,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=30),
        yaxis_title="",
        xaxis_title="",
        legend=dict(orientation="h", y=-0.2, x=0.2),
        yaxis=dict(showgrid=True, gridcolor="rgba(11, 26, 51, 0.08)", zerolinecolor="rgba(11,26,51,0.2)"),
    )

    with st.container():
        st.markdown("<div class='app-card netflow-card'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="app-card__header">
                <div>
                    <div class="pill">{series.subtitle}</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{series.title}</h3>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)


__all__ = ["MonthlyFlow", "NetFlowSeries", "render_yearly_net_flow"]
