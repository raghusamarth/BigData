# Stock Market Big Data Analytics (MongoDB + PySpark)

Upgraded from paper-trading demo → Big Data platform. All old features preserved and fixed.

## Fixes vs old project
- `main.py` now mounts `stocks`, `trade`, `analytics`, `pipeline` (old mounted only `auth`)
- `trade.py` fixed `ObjectId` bug (`find_one({"_id": str})` never matched), added `sell`, holdings tracking, portfolio
- `utils/fetch_stock_data.py` was empty → real yfinance bulk + incremental ingest
- Added time-series `historical_prices`, `stocks_meta`, `technical_indicators`, `analytics_results` + indexes

## Quickstart (local, needs MongoDB on localhost:27017)
```powershell
cd backend
..\.venv\Scripts\python -m pip install -r requirements.txt
..\.venv\Scripts\python -c "from database import ensure_time_series_collection, ensure_indexes; ensure_time_series_collection(); ensure_indexes(); print('mongo ok')"
..\.venv\Scripts\python -m jobs.ingest_bulk --period 10y          # ~30 symbols, ~75k docs
..\.venv\Scripts\python -m jobs.compute_indicators
..\.venv\Scripts\python jobs/spark_correlation.py --pandas-only   # no Java needed; omit flag to use real Spark
..\.venv\Scripts\python -m uvicorn main:app --reload              # API :8000
# new terminal:
..\.venv\Scripts\python -m streamlit run ../dashboard/app.py      # UI
```
Daily delta: `python -m jobs.ingest_incremental`

## Docker (needs Docker Desktop running)
```
docker compose up --build
```

## 5 Vs
Volume ~75k-1M real OHLCV docs · Velocity daily watermark ingest · Variety prices+fundamentals+indicators+txns · Veracity clean_ohlcv (NaN, high<low, dupes) + reports · Value sector/correlation/anomaly APIs.

## Viva cheat-sheet
- Why Mongo? time-series compression + flexible fundamentals + in-DB `$group/$lookup`.
- Mongo vs Spark: Mongo prunes/filters (monthly, top-N); Spark does full-scan correlation/clustering.
- Indexes: `(symbol,timestamp)` unique (range dedupe), `sector`, `(type,computedAt)`.
- Scale 1K→1M: same code, add partitions/symbols, cache in `analytics_results`.
