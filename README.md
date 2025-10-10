# Spending Analyser (scaffold)

This repository is a scaffold for a Streamlit-based spending analysis app.

Structure: The project contains packages for the Streamlit UI (`app/`), core business logic (`core/`), analytics, visualization, configuration, and tests.

This README intentionally contains no implementation details — it's a scaffold only.

## Quick start

To explore the Trading212-inspired dashboard scaffold locally:

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

The layout renders demo data so you can iterate on the UI before connecting the backend services.

## Enabling AI insights

The hero summary card at the top of the dashboard now supports four AI-powered focus modes: General overview, Category breakdown, Subscription spotlight, and Recurring commitments. The guidance adapts to the transactions you load.

To unlock OpenAI-generated copy, provide an API key via Streamlit secrets:

1. Create `.streamlit/secrets.toml` (already scaffolded in this repo) and set:
	```toml
	OPENAI_API_KEY = "sk-your-key"
	```
2. Restart the Streamlit app so the new secret is picked up.

If no key is available, the app falls back to on-device heuristics so you always see sensible guidance.
