"""AI summary hero card component for the Streamlit dashboard scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import streamlit as st


@dataclass(frozen=True)
class AISummary:
    """Structured content for the AI summary hero card."""

    headline: str
    supporting_points: Sequence[str]
    focus_options: Sequence[str]
    default_focus: str


def render_ai_summary(summary: AISummary) -> str:
    """Render the AI summary hero card and return the selected focus."""

    focus_key = "ai_focus"
    focus_selection = st.session_state.get(focus_key, summary.default_focus)

    try:
        default_index = summary.focus_options.index(focus_selection)
    except ValueError:
        try:
            default_index = summary.focus_options.index(summary.default_focus)
        except ValueError:
            default_index = 0
    with st.container():
        st.markdown("<div class='ai-summary-controls'>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="ai-summary-controls__row">
                <div>
                    <div class="ai-summary-controls__label">Where should we focus?</div>
                    <p class="ai-summary-controls__helper">Switch perspectives to explore different coaching angles.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        focus_selection = st.radio(
            "Focus selector",
            summary.focus_options,
            index=default_index if summary.focus_options else 0,
            horizontal=True,
            key=focus_key,
            label_visibility="collapsed",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='ai-summary-card'><div class='ai-summary-card__inner'>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="ai-summary-card__header">
                <span class="ai-summary-card__label">AI summary</span>
                <h2 style="margin: 0; font-weight: 600; font-size: 2rem;">Let's stay on track</h2>
                <p style="margin: 0; opacity: 0.75; font-size: 0.95rem;">
                    Guidance tailored from your latest spending signals.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div class='ai-summary-card__headline'>{summary.headline}</div>",
            unsafe_allow_html=True,
        )

        if summary.supporting_points:
            bullet_items = "".join(
                f"<li>{point}</li>" for point in summary.supporting_points
            )
            st.markdown(
                f"<ul>{bullet_items}</ul>",
                unsafe_allow_html=True,
            )

        st.markdown("</div></div>", unsafe_allow_html=True)

    return focus_selection


__all__ = ["AISummary", "render_ai_summary"]
