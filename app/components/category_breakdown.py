"""Category breakdown visual components."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import pandas as pd
import plotly.express as px
import streamlit as st


@dataclass(frozen=True)
class CategorySlice:
    name: str
    value: float
    share: float
    change: float | None = None
    is_positive: bool | None = None
    color: str | None = None

    @property
    def formatted_value(self) -> str:
        return f"£{self.value:,.0f}"

    @property
    def formatted_share(self) -> str:
        return f"{self.share:.0f}%"

    @property
    def formatted_change(self) -> str | None:
        if self.change is None:
            return None
        arrow = "▲" if (self.is_positive or False) else "▼"
        return f"{arrow} {abs(self.change):.1f}%"


@dataclass(frozen=True)
class CategoryBreakdown:
    title: str
    subtitle: str
    slices: Sequence[CategorySlice]


def render_category_breakdown_chart(breakdown: CategoryBreakdown) -> None:
    """Render the category breakdown pie chart."""

    names = [slice.name for slice in breakdown.slices]
    values = [slice.value for slice in breakdown.slices]
    raw_colors = [slice.color for slice in breakdown.slices]

    default_palette = [
        "#0051ff",
        "#3c79ff",
        "#00c2ff",
        "#7f8cff",
        "#0b1a33",
        "#2f3e60",
    ]
    colors = [
        raw_colors[idx]
        if isinstance(raw_colors[idx], str)
        else default_palette[idx % len(default_palette)]
        for idx in range(len(raw_colors))
    ]

    df = pd.DataFrame({"name": names, "value": values})

    fig = px.pie(
        df,
        values="value",
        names="name",
        color_discrete_sequence=colors,
        hole=0.5,
    )
    fig.update_traces(
        textfont=dict(size=16),
        textposition="inside",
        sort=False,
        hovertemplate="%{label}: £%{value:,.0f}<extra></extra>",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.2),
    )

    with st.container():
        st.markdown("<div class='app-card'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="app-card__header">
                <div>
                    <div class="pill">{breakdown.subtitle}</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.4rem; font-weight: 600;">{breakdown.title}</h3>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)


def render_category_breakdown_details(breakdown: CategoryBreakdown) -> None:
    """Render numeric details for each category."""

    with st.container():
        st.markdown("<div class='app-card breakdown-details'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="app-card__header">
                <div>
                    <div class="pill">Breakdown</div>
                    <h3 style="margin: 0.35rem 0 0; font-size: 1.3rem; font-weight: 600;">Where money went</h3>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div class='stat-list'>", unsafe_allow_html=True)
        for slice in breakdown.slices:
            change = slice.formatted_change
            if change:
                direction = "up" if (slice.is_positive is True) else "down"
                change_html = (
                    f"<span class='stat-list__change stat-list__change--{direction}'>{change}</span>"
                )
            else:
                change_html = ""
            st.markdown(
                f"""
                <div class='stat-list__item'>
                    <div>
                        <div class='stat-list__label'>{slice.name}</div>
                        <div class='stat-list__value'>{slice.formatted_value}</div>
                    </div>
                    <div class='stat-list__meta'>
                        <span>{slice.formatted_share}</span>
                        {change_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


__all__ = [
    "CategorySlice",
    "CategoryBreakdown",
    "render_category_breakdown_chart",
    "render_category_breakdown_details",
]
