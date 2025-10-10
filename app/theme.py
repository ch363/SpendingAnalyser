"""Streamlit theming utilities for the Trading212-inspired dashboard scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

import streamlit as st


@dataclass(frozen=True)
class Palette:
	"""Color palette inspired by Trading212's visual identity."""

	background: str = "#f4f6fb"
	surface: str = "#ffffff"
	surface_alt: str = "#f0f3ff"
	primary: str = "#0051ff"
	primary_light: str = "#3c79ff"
	accent: str = "#00c2ff"
	border: str = "#d8e1f8"
	text_primary: str = "#0b1a33"
	text_secondary: str = "#4c5c7a"
	success: str = "#00b386"
	warning: str = "#ff9f1c"


PALETTE = Palette()


def build_global_css(palette: Palette = PALETTE) -> str:
	"""Return bespoke CSS to tighten Streamlit's default styling."""

	return dedent(
		f"""
		:root {{
			--app-bg: {palette.background};
			--app-surface: {palette.surface};
			--app-surface-alt: {palette.surface_alt};
			--app-primary: {palette.primary};
			--app-primary-light: {palette.primary_light};
			--app-accent: {palette.accent};
			--app-border: {palette.border};
			--app-text: {palette.text_primary};
			--app-text-muted: {palette.text_secondary};
			--app-success: {palette.success};
			--app-warning: {palette.warning};
			--card-radius: 18px;
		}}

		body {{
			font-family: "Inter", "SF Pro Display", "Helvetica", sans-serif;
			background: var(--app-bg);
			color: var(--app-text);
		}}

		.stApp {{
			background: var(--app-bg);
		}}

		.app-card {{
			background: linear-gradient(145deg, rgba(255,255,255,0.9), rgba(245,247,255,0.9));
			border-radius: var(--card-radius);
			border: 1px solid var(--app-border);
			padding: 1.5rem;
			box-shadow: 0 20px 35px rgba(15, 26, 51, 0.08);
		}}

		.app-card--primary {{
			background: linear-gradient(160deg, var(--app-primary), var(--app-primary-light));
			border: none;
			color: white;
			box-shadow: 0 25px 40px rgba(0, 81, 255, 0.25);
		}}

		.ai-summary-card {{
			background: linear-gradient(165deg, var(--app-primary), var(--app-primary-light) 70%, rgba(0, 194, 255, 0.6));
			border-radius: 24px;
			padding: 2rem;
			color: white;
			position: relative;
			overflow: hidden;
		}}

		.ai-summary-card:before {{
			content: "";
			position: absolute;
			inset: 12px;
			border-radius: 20px;
			border: 1px solid rgba(255, 255, 255, 0.2);
			pointer-events: none;
		}}

		.ai-summary-card__inner {{
			position: relative;
			z-index: 1;
		}}

		.ai-summary-controls {{
			margin-bottom: 1.4rem;
			display: flex;
			flex-direction: column;
			gap: 0.5rem;
			padding: 0.8rem 1.1rem 1.2rem;
			background: rgba(255, 255, 255, 0.5);
			border-radius: 18px;
			border: 1px solid rgba(216, 225, 248, 0.7);
			box-shadow: 0 12px 24px rgba(15, 26, 51, 0.05);
		}}

		.ai-summary-controls__row {{
			display: flex;
			justify-content: space-between;
			align-items: center;
		}}

		.ai-summary-controls__label {{
			font-size: 0.78rem;
			text-transform: uppercase;
			letter-spacing: 0.08em;
			color: var(--app-text-muted);
		}}

		.ai-summary-controls__helper {{
			margin: 0.25rem 0 0;
			font-size: 0.9rem;
			color: var(--app-text-muted);
		}}

		.ai-summary-controls .stRadio > label {{
			font-weight: 500;
			color: var(--app-text);
		}}

		.ai-summary-controls .stRadio div[role="radiogroup"] {{
			gap: 1.25rem;
		}}

		.ai-summary-controls .stRadio div[role="radiogroup"] > label {{
			background: rgba(0, 81, 255, 0.08);
			padding: 0.45rem 0.9rem;
			border-radius: 999px;
			border: 1px solid transparent;
		}}

		.ai-summary-controls .stRadio div[role="radiogroup"] > label[data-checked="true"] {{
			background: var(--app-primary);
			color: white;
			border-color: rgba(0, 81, 255, 0.4);
			font-weight: 600;
			box-shadow: 0 10px 18px rgba(0, 81, 255, 0.2);
		}}

		.ai-summary-card__header {{
			display: flex;
			flex-direction: column;
			gap: 0.6rem;
		}}

		.ai-summary-card__label {{
			display: inline-flex;
			background: rgba(255, 255, 255, 0.16);
			padding: 0.35rem 0.9rem;
			border-radius: 999px;
			font-size: 0.75rem;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			width: fit-content;
		}}

		.ai-summary-card__headline {{
			margin-top: 1.8rem;
			font-size: 1.8rem;
			font-weight: 600;
		}}

		.ai-summary-card ul {{
			margin: 1.1rem 0 0 1.2rem;
			line-height: 1.6;
			opacity: 0.95;
		}}

		.snapshot-card {{
			background: white;
			border-radius: 24px;
			padding: 1.8rem;
			box-shadow: 0 20px 35px rgba(15, 26, 51, 0.08);
			border: 1px solid rgba(216, 225, 248, 0.8);
			display: grid;
			gap: 1.6rem;
		}}

		.snapshot-card__header {{
			display: flex;
			justify-content: space-between;
			align-items: center;
		}}

		.snapshot-card__badge {{
			background: rgba(60, 121, 255, 0.12);
			color: var(--app-primary);
			padding: 0.35rem 0.8rem;
			border-radius: 999px;
			font-size: 0.78rem;
			font-weight: 600;
		}}

		.snapshot-card__primary {{
			display: flex;
			justify-content: space-between;
			align-items: flex-end;
		}}

		.snapshot-card__primary-value {{
			font-size: 2.4rem;
			font-weight: 600;
		}}

		.snapshot-card__primary-delta {{
			font-size: 0.95rem;
			font-weight: 500;
			margin-top: 0.35rem;
		}}

		.snapshot-grid {{
			display: grid;
			gap: 1.2rem;
			grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
		}}

		.snapshot-metric__label {{
			font-size: 0.85rem;
			text-transform: uppercase;
			letter-spacing: 0.08em;
			color: var(--app-text-muted);
		}}

		.snapshot-metric__value {{
			margin-top: 0.45rem;
			font-size: 1.3rem;
			font-weight: 600;
			color: var(--app-text);
		}}

		.snapshot-metric__delta {{
			margin-top: 0.2rem;
			font-size: 0.9rem;
			font-weight: 500;
		}}

		.stat-list {{
			display: grid;
			gap: 1rem;
		}}

		.stat-list__item {{
			display: flex;
			justify-content: space-between;
			align-items: center;
			border: 1px solid var(--app-border);
			border-radius: 14px;
			padding: 0.9rem 1.1rem;
			background: var(--app-surface-alt);
		}}

		.stat-list__label {{
			font-size: 0.95rem;
			color: var(--app-text-muted);
		}}

		.stat-list__value {{
			font-size: 1.2rem;
			font-weight: 600;
			margin-top: 0.2rem;
		}}

		.stat-list__meta {{
			display: flex;
			align-items: center;
			gap: 0.8rem;
			font-weight: 600;
		}}

		.stat-list__change {{
			font-size: 0.85rem;
		}}

		.stat-list__change--up {{
			color: var(--app-success);
		}}

		.stat-list__change--down {{
			color: var(--app-warning);
		}}

		.subscriptions-card__totals {{
			display: flex;
			flex-direction: column;
			align-items: flex-end;
			gap: 0.1rem;
			font-weight: 600;
		}}

		.subscriptions-card__totals small {{
			font-weight: 500;
			color: rgba(11, 26, 51, 0.6);
		}}

		.table-list {{
			display: flex;
			flex-direction: column;
			gap: 0.6rem;
		}}

		.table-list__header,
		.table-list__row {{
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
			gap: 0.6rem;
			align-items: center;
			font-size: 0.95rem;
		}}

		.table-list__header {{
			font-size: 0.8rem;
			text-transform: uppercase;
			letter-spacing: 0.08em;
			color: var(--app-text-muted);
		}}

		.table-list__header span,
		.table-list__row span {{
			display: flex;
			align-items: center;
		}}

		.table-list__row span:last-child,
		.table-list__header span:last-child {{
			justify-content: flex-end;
		}}

		.table-list__row span:nth-last-child(2),
		.table-list__header span:nth-last-child(2) {{
			justify-content: center;
		}}

		.table-list__row {{
			background: var(--app-surface-alt);
			border-radius: 12px;
			padding: 0.75rem 0.9rem;
			border: 1px solid var(--app-border);
		}}

		.table-list--subscriptions .table-list__row,
		.table-list--subscriptions .table-list__header {{
			grid-template-columns: 2fr 1fr 1fr 1fr;
		}}

		.table-list--recurring .table-list__row,
		.table-list--recurring .table-list__header {{
			grid-template-columns: 1.5fr 1fr 1fr 0.8fr 1fr;
		}}

		.badge {{
			display: inline-flex;
			align-items: center;
			padding: 0.25rem 0.6rem;
			border-radius: 999px;
			font-size: 0.75rem;
			font-weight: 600;
		}}

		.badge--ok {{
			background: rgba(0, 179, 134, 0.12);
			color: var(--app-success);
		}}

		.badge--warn {{
			background: rgba(255, 159, 28, 0.14);
			color: var(--app-warning);
		}}

		.app-card__header {{
			display: flex;
			justify-content: space-between;
			align-items: center;
			margin-bottom: 1rem;
		}}

		.pill {{
			background: rgba(255, 255, 255, 0.16);
			padding: 0.35rem 0.8rem;
			border-radius: 999px;
			font-size: 0.75rem;
			letter-spacing: 0.04em;
			text-transform: uppercase;
		}}

		.metric-grid {{
			display: grid;
			grid-template-columns: repeat(2, minmax(0, 1fr));
			gap: 1rem;
		}}

		.metric {{
			background: rgba(255,255,255,0.75);
			border-radius: 14px;
			border: 1px solid rgba(255,255,255,0.25);
			padding: 1rem;
		}}

		.metric__label {{
			color: var(--app-text-muted);
			font-size: 0.8rem;
			text-transform: uppercase;
			letter-spacing: 0.08em;
		}}

		.metric__value {{
			font-size: 1.6rem;
			font-weight: 600;
			margin-top: 0.35rem;
		}}

		.metric__delta {{
			margin-top: 0.2rem;
			font-size: 0.9rem;
		}}

		.budget-status {{
			display: grid;
			gap: 1rem;
		}}

		.budget-status__indicator {{
			display: inline-flex;
			align-items: center;
			gap: 0.5rem;
			font-weight: 500;
		}}

		.budget-status__dot {{
			width: 12px;
			height: 12px;
			border-radius: 50%;
		}}

		.budget-status__dot--ontrack {{
			background: var(--app-success);
			box-shadow: 0 0 0 4px rgba(0, 179, 134, 0.2);
		}}

		.budget-status__dot--offtrack {{
			background: var(--app-warning);
			box-shadow: 0 0 0 4px rgba(255, 159, 28, 0.2);
		}}

		.stSlider > div[data-baseweb="slider"] {{
			color: var(--app-text);
		}}

		.stSlider .st-c2 {{
			background: var(--app-primary);
		}}

		.stSlider .st-c0 {{
			background: rgba(0, 81, 255, 0.2);
		}}

		.stTextInput > div > div > input {{
			border-radius: 12px;
			border: 1px solid var(--app-border) !important;
		}}

		.stRadio > label {{
			font-weight: 500;
			color: inherit;
		}}
		"""
	)


def apply_theme() -> None:
	"""Inject custom CSS into the current Streamlit app."""

	st.markdown(f"<style>{build_global_css()}</style>", unsafe_allow_html=True)


__all__ = ["PALETTE", "Palette", "apply_theme", "build_global_css"]
