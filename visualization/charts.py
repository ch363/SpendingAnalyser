"""Plotly chart builders for the PlainSpend dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .theme import theme_tokens
from app.theme import FONT_STACK

TOKENS = theme_tokens()

__all__ = [
    "build_category_chart",
    "build_vendor_chart",
]

def build_category_chart(category_df: pd.DataFrame) -> go.Figure:
    """Render a donut chart for category spend distribution using Plotly."""

    palette = list(TOKENS.category_palette)

    if category_df.empty:
        empty = pd.DataFrame({"Category": [], "CurrentValue": []})
        fig = px.pie(empty, names="Category", values="CurrentValue", hole=0.55)
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        return fig

    data = category_df.sort_values("CurrentValue", ascending=False).reset_index(drop=True)
    if len(data) > len(palette):
        repeats = (len(data) // len(palette)) + 1
        color_sequence = (palette * repeats)[: len(data)]
    else:
        color_sequence = palette[: len(data)]

    fig = px.pie(
        data,
        names="Category",
        values="CurrentValue",
        hole=0.55,
        color="Category",
        color_discrete_sequence=color_sequence,
    )

    hover_text = []
    text_positions: list[str] = []
    for _, row in data.iterrows():
        current_val = row.get("CurrentValue", 0.0)
        share_val = row.get("Share", 0.0)
        change_amt = row.get("ChangeAmount", 0.0)
        change_pct = row.get("PctChange", 0.0)

        # Guard against NaN/None values when formatting
        current_val = 0.0 if pd.isna(current_val) else float(current_val)
        share_val = 0.0 if pd.isna(share_val) else float(share_val)
        change_amt = 0.0 if pd.isna(change_amt) else float(change_amt)
        change_pct = 0.0 if pd.isna(change_pct) else float(change_pct)

        # Use outside labels (with leader lines) for tiny slices to keep them legible
        text_positions.append("inside" if share_val >= 0.055 else "outside")

        hover_text.append(
            f"{row['Category']}<br>"
            f"Spend: £{current_val:,.0f}<br>"
            f"Share: {share_val:.1%}<br>"
            f"Change: £{change_amt:,.0f}<br>"
            f"Change %: {change_pct:+.1%}"
        )

    fig.update_traces(
        textposition=text_positions,
        texttemplate="%{label}<br>%{percent:.1%}",
        insidetextfont=dict(family=FONT_STACK, color=TOKENS.neutral_white, size=14),
        outsidetextfont=dict(family=FONT_STACK, color=TOKENS.label_color, size=13),
        hoverinfo="text",
        hovertext=hover_text,
        marker=dict(line=dict(color=TOKENS.neutral_white, width=2)),
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            title="",
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05,
            font=dict(color=TOKENS.label_color, family=FONT_STACK, size=TOKENS.label_size),
        ),
        font=dict(family=FONT_STACK, color=TOKENS.label_color, size=TOKENS.label_size),
        hoverlabel=dict(font=dict(family=FONT_STACK, color=TOKENS.label_color, size=TOKENS.label_size)),
        showlegend=True,
    )

    return fig


def build_vendor_chart(vendor_df: pd.DataFrame) -> go.Figure:
    """Render a horizontal bar chart for vendor spend within a category using Plotly."""

    if vendor_df.empty:
        empty = pd.DataFrame({"label": [], "amount": []})
        fig = px.bar(empty, x="amount", y="label", orientation="h")
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        return fig

    vendor_df = vendor_df.copy()
    vendor_df["formatted_amount"] = vendor_df["amount"].map(lambda x: f"£{x:,.0f}")
    vendor_df["formatted_share"] = vendor_df["share"].map(lambda x: f"{x:.1%}")

    # Wrap long vendor labels onto two lines to prevent clipping/overlap
    def _wrap_label(label: str, max_len: int = 24) -> str:
        if not isinstance(label, str):
            return str(label)
        if len(label) <= max_len:
            return label
        # Try to break on the last space before the limit; otherwise hard break
        cut = label.rfind(" ", 0, max_len)
        if cut == -1:
            cut = max_len
        return label[:cut] + "<br>" + label[cut:].strip()

    vendor_df["label_wrapped"] = vendor_df["label"].apply(_wrap_label)

    fig = px.bar(
        vendor_df,
        x="amount",
        y="label_wrapped",
        orientation="h",
        text="formatted_amount",
        color_discrete_sequence=[TOKENS.vendor_bar_color],
    )

    fig.update_traces(
        hovertemplate=(
            "%{y}<br>Spend: %{text}<br>% of category: %{customdata[0]}<extra></extra>"
        ),
        customdata=vendor_df[["formatted_share"]].to_numpy(),
        textposition="outside",
        textfont=dict(family=FONT_STACK, color=TOKENS.label_color, size=TOKENS.label_size),
        cliponaxis=False,
    )

    # Dynamic height to reduce overlap; larger margins to avoid label clipping
    n_bars = int(vendor_df.shape[0])
    dynamic_height = max(260, 34 * n_bars + 80)
    fig.update_layout(
        margin=dict(l=160, r=90, t=30, b=20),
        xaxis=dict(title="Spend (£)", showgrid=False, zeroline=False, automargin=True),
        yaxis=dict(title="Merchant", automargin=True),
        bargap=0.35,
        height=dynamic_height,
        font=dict(family=FONT_STACK, color=TOKENS.label_color, size=TOKENS.label_size),
        hoverlabel=dict(font=dict(family=FONT_STACK, color=TOKENS.label_color, size=TOKENS.label_size)),
    )

    # Ensure labels outside bars aren't clipped by the plotting area
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)

    return fig
