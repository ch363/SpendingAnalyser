"""AI summary hero card component for the Streamlit dashboard scaffold."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import streamlit as st
from core.models import AISummary


def render_ai_summary(summary: AISummary | Mapping[str, object]) -> str:
    """Render the AI summary hero card and return the selected focus."""
    focus_key = "ai_focus"

    if isinstance(summary, Mapping):
        focus_options_raw = summary.get("focus_options")
    else:
        focus_options_raw = getattr(summary, "focus_options", None)
    if isinstance(focus_options_raw, Sequence) and not isinstance(focus_options_raw, (str, bytes)):
        focus_options = tuple(str(option) for option in focus_options_raw if str(option).strip()) or ("Default",)
    elif focus_options_raw:
        focus_options = (str(focus_options_raw),)
    else:
        focus_options = ("Default",)

    if isinstance(summary, Mapping):
        default_focus_raw = summary.get("default_focus")
    else:
        default_focus_raw = getattr(summary, "default_focus", None)
    default_focus = str(default_focus_raw) if default_focus_raw else focus_options[0]

    # Get current selection or fall back to default
    focus_selection = st.session_state.get(focus_key, default_focus)
    if focus_selection not in focus_options:
        focus_selection = default_focus
        st.session_state[focus_key] = focus_selection

    # --- Controls header (single HTML block) ---
    with st.container():
        st.markdown(
            """
            <div class="ai-summary-controls">
              <div class="ai-summary-controls__row">
                <div>
                  <div class="ai-summary-controls__label">Where should we focus?</div>
                  <p class="ai-summary-controls__helper">
                    Switch perspectives to explore different coaching angles.
                  </p>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if focus_options:
            style_injected_key = "ai_summary_focus_style_injected"
            if not st.session_state.get(style_injected_key):
                st.markdown(
                    """
                    <style>
                    [data-testid="stSegmentedControl"] button {
                        border-radius: 0.75rem !important;
                        padding: 0.65rem 1.1rem !important;
                        font-weight: 600 !important;
                        transition: all 0.2s ease-in-out !important;
                    }
                    [data-testid="stSegmentedControl"] button[data-selected="true"],
                    [data-testid="stSegmentedControl"] button[aria-pressed="true"] {
                        background: linear-gradient(135deg, #2f6bff, #4ac7ff) !important;
                        color: #ffffff !important;
                        box-shadow: 0 10px 20px rgba(47, 107, 255, 0.25) !important;
                        border: none !important;
                    }
                    [data-testid="stSegmentedControl"] button[data-selected="false"],
                    [data-testid="stSegmentedControl"] button[aria-pressed="false"] {
                        background: rgba(255,255,255,0.08) !important;
                        color: var(--app-text-muted, #334155) !important;
                        border: 1px solid rgba(148, 163, 184, 0.35) !important;
                    }
                    [data-testid="stSegmentedControl"] div[role="radiogroup"] {
                        gap: 0.75rem !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True,
                )
                st.session_state[style_injected_key] = True

            if hasattr(st, "segmented_control"):
                selected_option = st.segmented_control(
                    "Focus selector",
                    options=list(focus_options),
                    default=focus_selection,
                    key=f"{focus_key}_segmented",
                    label_visibility="collapsed",
                    format_func=str,
                )
            else:
                try:
                    default_index = list(focus_options).index(focus_selection)
                except ValueError:
                    default_index = 0
                selected_option = st.radio(
                    "Focus selector",
                    options=list(focus_options),
                    index=default_index,
                    horizontal=True,
                    key=f"{focus_key}_radio",
                    label_visibility="collapsed",
                )

            if selected_option:
                focus_selection = selected_option

        st.session_state[focus_key] = focus_selection

    # Resolve selected focus content with sensible fallback ordering
    if isinstance(summary, Mapping):
        focus_summaries = summary.get("focus_summaries")
    else:
        focus_summaries = getattr(summary, "focus_summaries", None)
    if not isinstance(focus_summaries, Mapping):
        focus_summaries = {}

    focus_content = focus_summaries.get(focus_selection)
    if focus_content is None:
        focus_content = focus_summaries.get(default_focus)
    if focus_content is None and focus_summaries:
        focus_content = next(iter(focus_summaries.values()))

    if focus_content and hasattr(focus_content, "headline"):
        headline_raw = getattr(focus_content, "headline")
    elif isinstance(focus_content, Mapping):
        headline_raw = focus_content.get("headline")
    else:
        headline_raw = None
    headline = str(headline_raw) if headline_raw else "Insights will appear here"

    if focus_content and hasattr(focus_content, "narrative"):
        narrative_raw = getattr(focus_content, "narrative")
    elif isinstance(focus_content, Mapping):
        narrative_raw = focus_content.get("narrative")
    else:
        narrative_raw = None
    narrative = str(narrative_raw) if narrative_raw else "Generate a summary to see narrative guidance."

    if focus_content and hasattr(focus_content, "supporting_points"):
        supporting_raw = getattr(focus_content, "supporting_points")
    elif isinstance(focus_content, Mapping):
        supporting_raw = focus_content.get("supporting_points")
    else:
        supporting_raw = ()
    if isinstance(supporting_raw, Sequence) and not isinstance(supporting_raw, (str, bytes)):
        supporting_points = tuple(str(point) for point in supporting_raw if str(point).strip())
    elif supporting_raw:
        supporting_points = (str(supporting_raw),)
    else:
        supporting_points = ()

    # --- Card (single HTML block) ---
    bullet_items_html = "".join(f"<li>{point}</li>" for point in supporting_points)
    card_html = f"""
    <div class='ai-summary-card'>
      <div class='ai-summary-card__inner'>
        <div class="ai-summary-card__header">
          <span class="ai-summary-card__label">AI summary</span>
          <h2 style="margin:0; font-weight:600; font-size:2rem;">Let's stay on track</h2>
          <p style="margin:0; opacity:0.75; font-size:0.95rem;">
            Guidance tailored from your latest spending signals.
          </p>
        </div>
        <div class='ai-summary-card__headline'>{headline}</div>
        <p class='ai-summary-card__narrative'>{narrative}</p>
        {f"<ul>{bullet_items_html}</ul>" if bullet_items_html else ""}
      </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    return focus_selection


__all__ = ["AISummary", "render_ai_summary"]
