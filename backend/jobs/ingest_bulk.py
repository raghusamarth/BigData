"""Bulk ingest: fetch years of OHLCV and upsert into Mongo.

Usage (from backend/ dir):
    python -m jobs.ingest_bulk --period 10y --interval 1d
    python -m jobs.ingest_bulk --symbols RELIANCE.NS AAPL --period 5y
"""
import argparse
import os
import sys

from pymongo import MongoClient

# Support `python -m jobs.ingest_bulk` from backend/ (and plain script run).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.symbols import ALL_SYMBOLS, EXCHANGE_MAP, SECTOR_MAP  # noqa: E402
from utils.fetch_stock_data import fetch_bulk  # noqa: E402
from utils.validation import to_documents, validate_doc  # noqa: E402

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "stock_analysis_db"


def get_db(uri=MONGO_URI):
    client = MongoClient(uri)
    db = client[DB_NAME]
    # Time-series collection for prices (falls back gracefully).
    try:
        db.create_collection(
            "historical_prices",
            timeseries={"timeField": "timestamp",
                        "metaField": "symbol", "granularity": "hours"},
        )
    except Exception:
        pass
    # No unique index: not supported on time-series collections.
    # Dedupe via upsert filter on (symbol, timestamp) in run().
    db["historical_prices"].create_index([("symbol", 1), ("timestamp", 1)])
    db["stocks_meta"].create_index("symbol", unique=True)
    return db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=ALL_SYMBOLS)
    ap.add_argument("--period", default="10y")
    ap.add_argument("--interval", default="1d")
    ap.add_argument("--mongo-uri", default=MONGO_URI)
    args = ap.parse_args()

    db = get_db(args.mongo_uri)
    prices, meta = db["historical_prices"], db["stocks_meta"]

    results = fetch_bulk(args.symbols, period=args.period, interval=args.interval)
    for symbol, (df, report) in results.items():
        print(f"{symbol}: {report}")
        if df is None or df.empty:
            continue
        # Upsert symbol metadata.
        meta.update_one(
            {"symbol": symbol},
            {"$set": {"symbol": symbol,
                      "sector": SECTOR_MAP.get(symbol, "Unknown"),
                      "exchange": EXCHANGE_MAP.get(symbol, "Unknown")}},
            upsert=True,
        )
        n = 0
        docs = [d for d in to_documents(symbol, df, interval=args.interval) if validate_doc(d)]
        if docs:
            # Time-series collections reject update_one upserts, so diff
            # against stored timestamps and insert only the new bars.
            have = {d["timestamp"] for d in prices.find(
                {"symbol": symbol}, {"timestamp": 1, "_id": 0})}
            fresh = [d for d in docs if d["timestamp"] not in have]
            if fresh:
                prices.insert_many(fresh, ordered=False)
            n = len(fresh)
        print(f"  inserted {n} new rows")


if __name__ == "__main__":
    main()
