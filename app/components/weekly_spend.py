"""Weekly spend chart component."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.models import WeeklySpendPoint, WeeklySpendSeries


def render_weekly_spend(series: WeeklySpendSeries) -> None:
    """Render spend by week bar chart."""

    df = pd.DataFrame(
        {
            "Week": [point.week_label for point in series.points],
            "Spend": [point.amount for point in series.points],
        }
    )

    fig = px.bar(
        df,
        x="Week",
        y="Spend",
        text="Spend",
        color_discrete_sequence=["#3c79ff"],
    )
    fig.update_traces(texttemplate="£%{text:,.0f}", textposition="outside", hovertemplate="%{x}: £%{y:,.0f}<extra></extra>")
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=30),
        yaxis_title="",
        xaxis_title="",
        yaxis=dict(showgrid=False, visible=False),
        xaxis=dict(showgrid=False),
    )

    with st.container():
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
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


__all__ = ["WeeklySpendPoint", "WeeklySpendSeries", "render_weekly_spend"]
