"""AI summary hero helper built on the shared `.hero` and `.pill` classes."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from textwrap import dedent

import streamlit as st


def render_ai_summary_card(summary_title: str, body: str, bullets: Sequence[str]) -> None:
    """Render the AI hero card with consistent typography and spacing."""

    sanitised_title = escape(summary_title) if summary_title else "AI insights"
    sanitised_body = escape(body) if body else "Connect your accounts to unlock personalised insights."
    bullet_items = "".join(f"<li>{escape(point)}</li>" for point in bullets if point and str(point).strip())
    bullet_list = f"<ul class='hero__actions'>{bullet_items}</ul>" if bullet_items else ""

    hero_html = dedent(
        f"""
        <section class="hero" role="region" aria-label="AI spending summary">
          <div class="hero__content">
            <span class="pill">AI summary</span>
            <h2 class="hero__heading">{sanitised_title}</h2>
            <p class="hero__body">{sanitised_body}</p>
            {bullet_list}
          </div>
        </section>
        """
    )
    st.markdown(hero_html, unsafe_allow_html=True)


__all__ = ["render_ai_summary_card"]
