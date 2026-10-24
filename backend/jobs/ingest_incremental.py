"""Incremental ingest: only fetch rows newer than the stored watermark.

Usage (from backend/ dir):
    python -m jobs.ingest_incremental
    python -m jobs.ingest_incremental --symbols TCS.NS MSFT --period 7d
"""
import argparse
import os
import sys

from pymongo import MongoClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.symbols import ALL_SYMBOLS  # noqa: E402
from utils.fetch_stock_data import fetch_symbol  # noqa: E402
from utils.validation import to_documents, validate_doc  # noqa: E402

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "stock_analysis_db"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=ALL_SYMBOLS)
    ap.add_argument("--period", default="7d")
    ap.add_argument("--interval", default="1d")
    ap.add_argument("--mongo-uri", default=MONGO_URI)
    args = ap.parse_args()

    db = MongoClient(args.mongo_uri)[DB_NAME]
    prices = db["historical_prices"]

    for symbol in args.symbols:
        # Watermark = latest stored timestamp for this symbol.
        latest = prices.find_one({"symbol": symbol}, sort=[("timestamp", -1)])
        watermark = latest["timestamp"] if latest else None
        print(f"{symbol}: watermark={watermark}")

        df, report = fetch_symbol(symbol, period=args.period, interval=args.interval)
        print(f"  fetch: {report}")
        if df is None or df.empty:
            continue
        docs = [d for d in to_documents(symbol, df, interval=args.interval)
                if validate_doc(d) and (watermark is None or d["timestamp"] > watermark)]
        n = 0
        if docs:
            # insert_many: time-series collections reject update_one upserts.
            prices.insert_many(docs, ordered=False)
            n = len(docs)
        print(f"  inserted {n} new rows")


if __name__ == "__main__":
    main()
