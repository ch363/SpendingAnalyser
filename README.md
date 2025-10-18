# Spending Analyser

A Streamlit dashboard for analysing personal spend: monthly snapshot, budget tracking, recurring bills, subscriptions, vendor/category breakdowns, and a short AI-generated summary.

## How it works

- UI (`app/`): Streamlit components render the dashboard, charts, and controls. Entry point is `app/main.py`.
	- `components/` houses the reusable card renderers (weekly spend, subscriptions, category insight, etc.) that embed Plotly charts via `components.html`.
- Core logic (`core/`):
	- `data_loader.py` loads a CSV of transactions (defaults to `data/fixtures/seed.csv`) and normalises columns.
	- `monthly_service.py` computes the Monthly Snapshot and Budget Tracker.
	- `summary_service.py` builds category/merchant summaries.
	- `core/ai` provides optional AI helpers for summaries and budget suggestions.
- Analytics (`analytics/`): Additional builders used by the dashboard (e.g. recurring detection, AI forecasting helpers, categorisation).
- Visualisation (`visualization/`): Plotly/Altair chart helpers and theme.

Data expectations (when replacing the demo CSV):
- Required columns: `date`, `amount`. Optional: `txn_id`, `is_refund`, `description` (or `merchant`), etc.
- Negative `amount` values are spend; positive values are income/refunds. Refunds can be flagged via `is_refund`.

## Run locally

1) Create and activate a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Start the app

```bash
streamlit run app/main.py
```

Optional (VS Code): use the built-in task “Run Streamlit app”.

The app regenerates the demo dataset (`data/fixtures/seed.csv`) with fresh synthetic transactions each time the Streamlit server starts. Set `SPENDING_ANALYSER_AUTO_SYNTH=0` before launching if you want to keep a custom CSV untouched.


## Enable AI insights (optional)

The hero card supports AI focus modes (overview, categories, subscriptions, recurring). To enable OpenAI-powered copy:

1) Create `.streamlit/secrets.toml` and add your key:

```toml
OPENAI_API_KEY = "sk-your-key"
```

2) Restart Streamlit. If no key is provided, the app falls back to local heuristics so the dashboard still works.

## Troubleshooting

- If Streamlit can’t find the CSV, ensure `data/fixtures/seed.csv` exists or update the loader to point at your file.
- If AI features don’t show, confirm `OPENAI_API_KEY` is set in `.streamlit/secrets.toml` and the app was restarted.
