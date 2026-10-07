# QuickBite Food-Delivery Analytics

An end-to-end data project that answers one question: **why do food-delivery orders get cancelled?**

Raw data → cleaned data → analysis-ready tables → KPIs and dashboard → cancellation model → plain-English SQL assistant.

## Architecture

```
generator/      synthetic raw data (users, restaurants, orders, app_events)
   │
   ▼
data/raw/  ──►  raw schema  ──►  staging schema  ──►  mart schema   (DuckDB: quickbite.duckdb)
                (as landed)      (cleaned, bad rows    orders_fact, users_dim,
                                  quarantined)         restaurants_dim
                                                          │
                          ┌───────────────┬───────────────┤
                          ▼               ▼               ▼
                   analytics/        model/          assistant/
                   KPI SQL +         cancellation    text-to-SQL
                   Streamlit         classifier      (Gemini)
```

| Layer | Contents |
|---|---|
| raw | Source tables exactly as generated, with duplicates and bad rows left in |
| staging | Deduplicated and typed; invalid orders go to `staging.orders_quarantine` instead of crashing the run |
| mart | `orders_fact`, `users_dim`, `restaurants_dim`: the tables every downstream piece reads |

Source volumes at full scale: 50,000 users, 500 restaurants, 500,000 orders, 5,000,000 app events. See [docs/design.md](docs/design.md) and the [table diagram](docs/table%20diagram.png).

## Project layout

| Path | Purpose |
|---|---|
| [generator/generate_data.py](generator/generate_data.py) | Seeded synthetic data generator (`--scale`, `--format` options) |
| [pipeline/](pipeline) | `load_raw.py`, `clean_staging.py`, `build_marts.py`, and `run_all.py` to orchestrate them |
| [analytics/kpi_queries.sql](analytics/kpi_queries.sql) | 10 KPI queries (orders per day, cancellation by hour and area, top restaurants, and more) |
| [analytics/dashboard.py](analytics/dashboard.py) | Streamlit dashboard |
| [model/](model) | `train.py` (logistic regression), `predict.py`, saved `.pkl` artifacts |
| [assistant/text_to_sql.py](assistant/text_to_sql.py) | Ask questions in English; Gemini writes the SQL, DuckDB runs it |
| [tests/test_pipeline.py](tests/test_pipeline.py) | pytest data-quality checks on the mart |

## Setup

Requires Python 3.10+ (developed on 3.13).

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

Run everything from the repository root.

**1. Build the pipeline** (generates data if `data/raw/` is empty, then load → clean → marts → tests):

```powershell
python pipeline/run_all.py
```

Logs go to `logs/pipeline.log`. A failed step or failed test writes to `logs/alerts.log` and, if `ALERT_WEBHOOK_URL` is set, posts to that Slack webhook.

For a quick small run, generate 1% of the data first:

```powershell
python generator/generate_data.py --scale 0.01
```

**2. Dashboard**

```powershell
streamlit run analytics/dashboard.py
```

**3. Train the cancellation model**

```powershell
python model/train.py
```

It uses order value, order hour, delivery minutes, restaurant rating, cuisine and device. The model is a class-balanced logistic regression, evaluated on a stratified 80/20 split. It prints precision and recall, and saves the model to `model/cancellation_model.pkl`.

**4. SQL assistant**

```powershell
$env:GEMINI_API_KEY = "your-key-here"
python assistant/text_to_sql.py
```

Then ask things like *"Which city area has the highest cancellation rate?"*

Safety: the model may only return a single `SELECT`/`WITH` query. A keyword filter rejects anything else, and the database is opened `read_only=True`, so writes are impossible even if the filter is bypassed.

## Tests

```powershell
python -m pytest tests/test_pipeline.py -q
```

Checks include no duplicate `order_id` values and no negative `order_value` in `mart.orders_fact`. `run_all.py` runs these automatically.

Set `DEMO_BREAK=1` when running `run_all.py` to inject a duplicate order on purpose and watch the tests and alert fire.

## Tech stack

Python, DuckDB, pandas, scikit-learn, Streamlit, pytest, Google Gemini (`google-genai`).
