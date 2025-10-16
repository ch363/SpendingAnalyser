"""Streamlit theming utilities for the Trading212-inspired dashboard scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

import streamlit as st


@dataclass(frozen=True)
class Palette:
	"""Color palette inspired by Trading212's visual identity."""

	background: str = "#fdfdfd"
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
			--app-bg: #f7f8fb;
			--app-text: #0f172a;
			--app-text-muted: #6b7280;
			--app-blue: #2563eb;
			--app-cyan: #38bdf8;
			--app-orange: #f59e0b;
			--app-green: #16a34a;
			--app-red: #dc2626;
			--card-bg: #ffffff;
			--card-border: rgba(148, 163, 184, 0.18);
			--app-surface: #ffffff;
			--app-surface-alt: #eef2ff;
			--app-primary: #2563eb;
			--app-primary-light: #60a5fa;
			--app-accent: #38bdf8;
			--app-border: rgba(148, 163, 184, 0.18);
			--app-success: {palette.success};
			--app-warning: {palette.warning};
			--focus-ring: rgba(37, 99, 235, 0.45);
			--card-radius: 1.5rem;
			--font-family: "Inter", "SF Pro Display", "Segoe UI", "Helvetica Neue", sans-serif;
		}}

		body {{
			font-family: "Inter", "SF Pro Display", "Helvetica", sans-serif;
			background: var(--app-bg);
			color: var(--app-text);
		}}

		.stApp {{
			background: var(--app-bg);
			color: var(--app-text);
		}}

		button, [role="button"], input, select {{
			font-family: inherit;
		}}

		button:focus-visible,
		[role="button"]:focus-visible,
		input:focus-visible,
		select:focus-visible,
		textarea:focus-visible {{
			outline: 2px solid var(--focus-ring);
			outline-offset: 2px;
		}}

		.app-shell {{
			max-width: 1240px;
			margin: 0 auto;
			padding: 1.25rem 1.25rem 2rem;
		}}

		.card {{
			background: var(--card-bg);
			border: 1px solid var(--card-border);
			border-radius: var(--card-radius);
			padding: 1.6rem;
			box-shadow: 0 25px 45px rgba(15, 23, 42, 0.07);
			display: grid;
			gap: 1.4rem;
		}}

		.hero {{
			background: linear-gradient(135deg, var(--app-blue), var(--app-cyan));
			color: #ffffff;
			padding: 1.8rem;
			border-radius: 1.4rem;
			position: relative;
			overflow: hidden;
		}}

		.hero::after {{
			content: "";
			position: absolute;
			inset: 12px;
			border-radius: 1.2rem;
			border: 1px solid rgba(255, 255, 255, 0.25);
			opacity: 0.7;
			pointer-events: none;
		}}

		.hero__content {{
			position: relative;
			z-index: 1;
			display: grid;
			gap: 1rem;
		}}

		.pill {{
			display: inline-flex;
			align-items: center;
			gap: 0.4rem;
			border-radius: 999px;
			padding: 0.25rem 0.7rem;
			font-weight: 600;
			font-size: 0.8rem;
			letter-spacing: 0.06em;
			text-transform: uppercase;
			background: rgba(15, 23, 42, 0.06);
			color: var(--app-text);
		}}

		.badge {{
			display: inline-flex;
			align-items: center;
			gap: 0.35rem;
			border-radius: 999px;
			padding: 0.25rem 0.6rem;
			font-size: 0.75rem;
			font-weight: 600;
			background: rgba(37, 99, 235, 0.1);
			color: var(--app-blue);
		}}

		.metrics {{
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
			gap: 1rem;
		}}

		.metric-label {{
			font-size: 0.8rem;
			letter-spacing: 0.06em;
			text-transform: uppercase;
			color: var(--app-text-muted);
		}}

		.metric-value {{
			font-size: 1.75rem;
			font-weight: 700;
			color: var(--app-text);
		}}

		.chip {{
			display: inline-flex;
			align-items: center;
			gap: 0.35rem;
			border-radius: 999px;
			padding: 0.2rem 0.6rem;
			font-size: 0.8rem;
			font-weight: 600;
		}}

		.chip--pos {{
			background: rgba(22, 163, 74, 0.12);
			color: var(--app-green);
		}}

		.chip--neg {{
			background: rgba(220, 38, 38, 0.12);
			color: var(--app-red);
		}}

		.status-dot {{
			width: 0.55rem;
			height: 0.55rem;
			border-radius: 999px;
			display: inline-block;
		}}

		.status--ok {{
			background: var(--app-green);
		}}

		.status--bad {{
			background: var(--app-orange);
		}}

		.toolbar {{
			display: flex;
			align-items: center;
			justify-content: space-between;
			gap: 0.8rem;
			background: var(--card-bg);
			border: 1px solid var(--card-border);
			border-radius: 1rem;
			padding: 0.7rem 1rem;
		}}

		.toolbar__label {{
			font-weight: 600;
			color: var(--app-text);
		}}

		.toolbar__helper {{
			font-size: 0.9rem;
			color: var(--app-text-muted);
		}}

		.hero__heading {{
			font-size: 2.1rem;
			font-weight: 600;
			margin: 0;
		}}

		.hero__body {{
			font-size: 1rem;
			margin: 0;
			line-height: 1.6;
		}}

		.hero__actions {{
			margin: 0;
			padding-left: 1.2rem;
			display: grid;
			gap: 0.4rem;
			font-size: 0.95rem;
			list-style: disc;
		}}

		.hero__actions li {{
			margin: 0;
			color: inherit;
		}}

		.section-title {{
			margin: 0;
			font-size: 1.6rem;
			font-weight: 600;
			color: var(--app-text);
		}}

		.page-subtitle {{
			margin: 0.35rem 0 0;
			font-size: 1rem;
			color: var(--app-text-muted);
		}}

		.page-meta {{
			margin-top: 0.75rem;
			font-size: 0.95rem;
			color: var(--app-text-muted);
			font-weight: 500;
		}}

		.input-helper {{
			margin: 0.4rem 0 0;
			font-size: 0.85rem;
			color: var(--app-text-muted);
		}}

		.snapshot-card {{
			display: grid;
			gap: 1.8rem;
		}}

		.snapshot-card--modern {{
			gap: 2rem;
		}}

		.snapshot-card__header {{
			display: flex;
			align-items: flex-start;
			justify-content: space-between;
			gap: 1.5rem;
		}}

		.snapshot-card__period {{
			display: inline-block;
			font-size: 0.85rem;
			letter-spacing: 0.12em;
			text-transform: uppercase;
			font-weight: 600;
			color: rgba(15, 23, 42, 0.6);
		}}

		.snapshot-card__title {{
			margin: 0.5rem 0 0;
			font-size: 2.15rem;
			font-weight: 700;
			color: var(--app-text);
		}}

		.snapshot-card__badge {{
			background: rgba(37, 99, 235, 0.14);
			color: var(--app-blue);
		}}

		.snapshot-card__primary {{
			display: grid;
			gap: 0.75rem;
		}}

		.snapshot-card__overline {{
			font-size: 0.78rem;
			letter-spacing: 0.14em;
			text-transform: uppercase;
			font-weight: 600;
			color: var(--app-text-muted);
		}}

		.snapshot-card__value-row {{
			display: flex;
			align-items: baseline;
			gap: 1.15rem;
			flex-wrap: wrap;
		}}

		.snapshot-card__value {{
			font-size: 2.6rem;
			font-weight: 700;
			color: var(--app-text);
		}}

		.snapshot-card__delta,
		.snapshot-card__metric-delta {{
			font-size: 1rem;
			font-weight: 600;
		}}

		.snapshot-card__delta--pos,
		.snapshot-card__metric-delta--pos {{
			color: var(--app-green);
		}}

		.snapshot-card__delta--neg,
		.snapshot-card__metric-delta--neg {{
			color: var(--app-orange);
		}}

		.snapshot-card__grid {{
			display: grid;
			gap: 1.4rem 2.1rem;
			/* Force two metrics per row on typical screens */
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}}

		/* On small screens, fall back to a single column for readability */
		@media (max-width: 640px) {{
			.snapshot-card__grid {{
				grid-template-columns: 1fr;
			}}
		}}

		.snapshot-card__metric {{
			display: grid;
			gap: 0.35rem;
		}}

		.snapshot-card__metric-label {{
			font-size: 0.8rem;
			letter-spacing: 0.1em;
			text-transform: uppercase;
			font-weight: 600;
			color: var(--app-text-muted);
		}}

		.snapshot-card__metric-value {{
			font-size: 1.35rem;
			font-weight: 600;
			color: var(--app-text);
		}}

		.snapshot-card__metric-delta {{
			font-size: 0.95rem;
			color: var(--app-text-muted);
		}}

		.budget-card__header {{
			display: flex;
			align-items: flex-start;
			justify-content: space-between;
			gap: 1.5rem;
		}}

		.budget-card__status {{
			display: inline-flex;
			align-items: center;
			gap: 0.55rem;
			font-weight: 600;
			color: var(--app-text);
		}}

		.budget-card__status-label {{
			font-size: 0.95rem;
		}}

		.budget-card__metrics {{
			gap: 1.2rem;
		}}

		.budget-card__control {{
			display: flex;
			flex-direction: column;
			gap: 0.35rem;
		}}

		.budget-card__control-title {{
			font-size: 0.78rem;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			font-weight: 600;
			color: var(--app-text-muted);
		}}

		.budget-card__control-helper {{
			margin: 0;
			font-size: 0.92rem;
			color: var(--app-text-muted);
		}}

		.budget-card__footer {{
			display: flex;
			justify-content: space-between;
			align-items: center;
			font-weight: 600;
			color: var(--app-text);
		}}

		/* Thin budget insights card */
		.budget-controls-card {{
			padding: 1rem 1.2rem;
			gap: 0.9rem;
			min-height: 200px;
		}}

		/* Uniform insight row cards */
		.uniform-insight-row {{
			display: grid;
			grid-auto-rows: 1fr;
			min-height: 200px;
		}}

		.budget-progress {{
			display: grid;
			gap: 0.65rem;
		}}

		.progress {{
			position: relative;
			height: 0.55rem;
			border-radius: 999px;
			background: rgba(148, 163, 184, 0.22);
			overflow: hidden;
		}}

		.progress__fill {{
			height: 100%;
			background: linear-gradient(90deg, var(--app-blue), var(--app-cyan));
			border-radius: inherit;
		}}

		.progress__legend {{
			display: flex;
			align-items: center;
			justify-content: space-between;
			font-size: 0.85rem;
			color: var(--app-text-muted);
		}}

		.progress__note {{
			margin: 0;
			font-size: 0.9rem;
			color: var(--app-text-muted);
		}}

		.layout-gap {{
			height: 1.6rem;
		}}

		/* Budget target card: style the block that contains the number input and its related content */
		div[data-testid="stVerticalBlock"]:has(div[data-testid="stNumberInput"]) {{
			background: var(--card-bg);
			border: 1px solid var(--card-border);
			border-radius: var(--card-radius);
			padding: 1rem 1.2rem;
			box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
			min-height: 200px;
			display: grid;
			gap: 0.6rem;
			align-content: start;
		}}

		/* Alternate hook: style any container that includes our scope marker */
		div[data-testid="stVerticalBlock"]:has(.budget-target-scope) {{
			background: var(--card-bg);
			border: 1px solid var(--card-border);
			border-radius: var(--card-radius);
			padding: 1rem 1.2rem;
			box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
			min-height: 200px;
			display: grid;
			gap: 0.6rem;
			align-content: start;
		}}

		div[data-testid="stNumberInput"] > label {{
			font-size: 0.78rem;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			font-weight: 600;
			color: var(--app-text-muted);
			margin-bottom: 0.35rem;
		}}

		div[data-testid="stNumberInput"] input {{
			border-radius: 0.85rem;
			border: 1px solid rgba(148, 163, 184, 0.4);
			padding: 0.55rem 0.8rem;
			font-weight: 600;
			color: var(--app-text);
			background: rgba(255, 255, 255, 0.9);
		}}

		div[data-testid="stDateInput"] > label {{
			font-weight: 600;
			font-size: 0.78rem;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			color: var(--app-text-muted);
			margin-bottom: 0.4rem;
		}}

		div[data-testid="stDateInput"] input {{
			border-radius: 0.85rem;
			border: 1px solid rgba(148, 163, 184, 0.4);
			padding: 0.5rem 0.75rem;
			font-weight: 600;
			color: var(--app-text);
		}}

		div[data-testid="stSelectbox"] > label {{
			font-weight: 600;
			font-size: 0.78rem;
			letter-spacing: 0.08em;
			text-transform: uppercase;
			color: var(--app-text-muted);
			margin-bottom: 0.35rem;
		}}

		div[data-testid="stSelectbox"] [data-baseweb="select"] {{
			border-radius: 0.85rem;
			border: 1px solid rgba(148, 163, 184, 0.4);
			background: rgba(255, 255, 255, 0.9);
			box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
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

		.category-insight {{
			max-width: 100%;
		}}

		.category-insight__surface {{
			background: #ffffff;
			border-radius: 28px;
			border: 1px solid rgba(216, 225, 248, 0.8);
			box-shadow: 0 30px 45px rgba(15, 26, 51, 0.08);
			padding: 0.6rem;
		}}

		.category-insight__surface-inner {{
			background: linear-gradient(180deg, rgba(244, 246, 255, 0.7), rgba(250, 251, 255, 0.95));
			border-radius: 22px;
			padding: 1.8rem;
		}}

		.category-insight__surface-body {{
			display: flex;
			flex-direction: column;
			gap: 2rem;
		}}

		.category-insight--empty {{
			align-items: center;
			text-align: center;
			gap: 1rem;
			padding: 2.2rem;
		}}

		.category-insight__intro {{
			display: flex;
			flex-direction: column;
			gap: 0.65rem;
		}}

		.category-insight__pill {{
			display: inline-flex;
			align-items: center;
			padding: 0.35rem 0.95rem;
			background: rgba(12, 111, 253, 0.12);
			color: var(--app-primary);
			border-radius: 999px;
			font-size: 0.78rem;
			font-weight: 600;
			letter-spacing: 0.08em;
			text-transform: uppercase;
		}}

		.category-insight__intro h2 {{
			margin: 0;
			font-size: 1.8rem;
			font-weight: 650;
			color: var(--app-text);
		}}

		.category-insight__total {{
			font-weight: 600;
			font-size: 1.05rem;
			color: var(--app-text-muted);
		}}

		.category-insight .stSelectbox > div {{
			background: rgba(255, 255, 255, 0.9);
			border-radius: 18px;
			padding: 0.35rem 0.8rem;
			border: 1px solid rgba(12, 111, 253, 0.24);
			box-shadow: 0 8px 18px rgba(12, 111, 253, 0.12);
		}}

		.category-insight .stSelectbox label {{
			font-size: 0.78rem;
			text-transform: uppercase;
			letter-spacing: 0.08em;
			color: var(--app-text-muted);
			font-weight: 600;
		}}

		.status-badge {{
			display: inline-flex;
			align-items: center;
			padding: 0.35rem 0.85rem;
			border-radius: 999px;
			font-size: 0.75rem;
			font-weight: 600;
			text-transform: uppercase;
			letter-spacing: 0.08em;
		}}

		.status-badge--improved {{
			background: rgba(34, 197, 94, 0.16);
			color: #15803d;
		}}

		.status-badge--higher {{
			background: rgba(249, 115, 22, 0.16);
			color: #c2410c;
		}}

		.status-badge--neutral {{
			background: rgba(148, 163, 184, 0.16);
			color: var(--app-text-muted);
		}}

		.category-detail-panel {{
			display: flex;
			flex-direction: column;
			gap: 1.5rem;
			margin-bottom: 1rem;
		}}

		.category-detail-panel__header {{
			display: flex;
			justify-content: space-between;
			align-items: flex-start;
			gap: 1rem;
		}}

		.category-detail-panel__header h4 {{
			margin: 0;
			font-size: 1.4rem;
			font-weight: 600;
		}}

		.category-detail-panel__range {{
			display: block;
			margin-top: 0.35rem;
			font-size: 0.9rem;
			color: var(--app-text-muted);
		}}

		.category-detail-panel__metrics {{
			display: grid;
			grid-template-columns: repeat(2, minmax(140px, 1fr));
			gap: 1.25rem;
		}}

		.metric-card {{
			background: linear-gradient(160deg, rgba(255,255,255,0.95), rgba(244,248,255,0.85));
			border-radius: 18px;
			padding: 1.1rem 1.35rem;
			display: flex;
			flex-direction: column;
			gap: 0.45rem;
			border: 1px solid rgba(216, 225, 248, 0.7);
			box-shadow: 0 12px 25px rgba(12, 52, 104, 0.08);
		}}

		.metric-card span {{
			font-size: 0.82rem;
			text-transform: uppercase;
			letter-spacing: 0.05em;
			color: var(--app-text-muted);
			font-weight: 600;
		}}

		.metric-card strong {{
			font-size: 1.45rem;
			font-weight: 650;
			color: var(--app-text);
		}}

		.metric-card small {{
			font-size: 0.88rem;
			color: var(--app-text-muted);
			font-weight: 600;
		}}

		.metric-card--delta {{
			background: rgba(12, 111, 253, 0.08);
			border-color: rgba(12, 111, 253, 0.18);
		}}

		.category-detail-panel__top-merchant {{
			display: flex;
			flex-direction: column;
			gap: 0.35rem;
		}}

		.category-detail-panel__top-merchant span {{
			font-size: 0.78rem;
			text-transform: uppercase;
			letter-spacing: 0.08em;
			color: var(--app-text-muted);
			font-weight: 600;
		}}

		.category-detail-panel__top-merchant p {{
			margin: 0;
			font-weight: 600;
			color: var(--app-text);
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
