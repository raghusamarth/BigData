# Stock Market Big Data Analytics Platform (MongoDB + PySpark)

Paper-trading app upgraded into a college Big Data Analytics system.
Frontend: **The Market Record** — Newsprint design (React + Tailwind).
Backend: FastAPI · MongoDB time-series · PySpark · Docker.

## 1. How It Works

```
yfinance (real OHLCV + fundamentals)
  → jobs/ingest_bulk.py — bulk load, clean_ohlcv() drops NaN / high<low / dupes
  → MongoDB `historical_prices` (TIME-SERIES: timestamp + symbol meta)
  → jobs/ingest_incremental.py — daily delta via max-timestamp watermark
  → jobs/compute_indicators.py — SMA/EMA/RSI/MACD/Bollinger → `technical_indicators`
  → Mongo Aggregation (monthly, top-gainers, sectors via $lookup, volatility, spikes)
  → jobs/spark_correlation.py — PySpark MLlib correlation + z-score anomalies → `analytics_results`
  → FastAPI (/stocks /trade /analytics /pipeline) → React Newsprint UI (:3000)
```

MongoDB does selective rollups where the data lives; Spark does the
full-scan O(n²) correlation. Old trading core (auth/buy) preserved, bugs fixed.

## 2. Execution

### Option A — Docker (recommended, verified working)

```powershell
cd C:\Users\raghu\Downloads\shit\DBMS_stock2
docker compose up -d --build        # mongo :27017, api :8000, frontend :3000
docker compose --profile seed run --rm seed   # full seed: 30 symbols × 5y + indicators + Spark job
```

Open: **http://localhost:3000** (UI) · **http://localhost:8000/docs** (API)

Quick smoke test instead of full seed (~1 min, 2 symbols):
```powershell
docker compose exec api python -m jobs.ingest_bulk --symbols AAPL MSFT --period 1mo
docker compose exec api python -m jobs.compute_indicators
docker compose exec api python jobs/spark_correlation.py --pandas-only
```

### Fast Big-Data seed (yfinance is slow — use this)

`jobs/seed_synth.py` generates realistic OHLCV offline with numpy
(GBM + market factor + sector drift/vol, volume spikes) in seconds.
Every doc is labeled `source="synthetic-gbm"`; real rows are never touched.

```powershell
docker compose exec api python -m jobs.seed_synth --wipe-synthetic
docker compose exec api python -m jobs.compute_indicators
docker compose exec api python jobs/spark_correlation.py --pandas-only
```
Defaults: 30 symbols × 15y daily + 8y hourly ≈ **~537K price docs,
~1M total with indicators**. Flags: `--years`, `--hourly-years`,
`--symbols`, `--seed`, `--wipe-synthetic` (idempotent re-runs).

Daily delta (velocity demo): `docker compose exec api python -m jobs.ingest_incremental`

Stop: `docker compose down` (add `-v` to wipe the database).

### Option B — Local (no Docker)

```powershell
# 1. MongoDB on localhost:27017, then:
cd backend
..\.venv\Scripts\python -m pip install -r requirements.txt
..\.venv\Scripts\python -m jobs.ingest_bulk --period 5y
..\.venv\Scripts\python -m jobs.compute_indicators
..\.venv\Scripts\python jobs/spark_correlation.py --pandas-only
..\.venv\Scripts\python -m uvicorn main:app --reload   # :8000
cd ..\frontend; npm install; npm run dev                # :5173 (proxies /api → :8000)
```

## 3. Viva Cheat-Sheet

| Q | A |
|---|---|
| Big Data? | ~75K–1M real OHLCV docs, 4 data varieties, incremental ingest, 1 distributed job |
| Why Mongo? | Time-series compression + flexible fundamentals + in-DB `$group/$lookup` |
| Mongo vs Spark | Mongo prunes (monthly/top-N); Spark does pairwise correlation/clustering |
| Indexes | `(symbol,timestamp)` plain (unique unsupported on TS collections), `sector`, `(type,computedAt)` |
| Dedupe | Python-side timestamp diff + `insert_many` (TS collections reject upserts) |
| 5 Vs | Volume docs count on /pipeline · Velocity watermark · Variety 4 types · Veracity clean report · Value correlation/anomaly APIs |

## 4. Layout

```
backend/  FastAPI routes/*, database.py, analytics/mongo_aggregations.py,
          utils/{fetch_stock_data,validation,indicators}.py,
          jobs/{ingest_bulk,ingest_incremental,compute_indicators,spark_correlation}.py
frontend/ React 19 + Tailwind Newsprint (src/components/*, src/api.js)
docker-compose.yml  mongo (healthcheck) → api → frontend + `seed` profile
```
