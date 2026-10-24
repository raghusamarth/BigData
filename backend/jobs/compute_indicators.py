"""Compute technical indicators per symbol and store in Mongo.

Usage (from backend/ dir):
    python -m jobs.compute_indicators
    python -m jobs.compute_indicators --symbols AAPL TCS.NS
"""
import argparse
import os
import sys

import pandas as pd
from pymongo import MongoClient, UpdateOne

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.symbols import ALL_SYMBOLS  # noqa: E402
from utils.indicators import add_all_indicators  # noqa: E402

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "stock_analysis_db"


def compute_for_symbol(prices_col, out_col, symbol: str) -> int:
    """Read one symbol's history, compute indicators, bulk-write. Returns row count."""
    cursor = prices_col.find({"symbol": symbol}).sort("timestamp", 1)
    rows = list(cursor)
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    # Map lowercase mongo fields -> Capitalised indicator inputs.
    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low",
                            "close": "Close", "volume": "Volume"})
    df = df.set_index("timestamp").sort_index()
    df = add_all_indicators(df)

    ops = []
    for ts, row in df.iterrows():
        doc = {"symbol": symbol, "timestamp": ts,
               "close": float(row["Close"]),
               "sma20": _f(row.get("sma20")), "sma50": _f(row.get("sma50")),
               "ema12": _f(row.get("ema12")), "ema26": _f(row.get("ema26")),
               "rsi14": _f(row.get("rsi14")),
               "macd": _f(row.get("macd")), "macd_signal": _f(row.get("macd_signal")),
               "bb_upper": _f(row.get("bb_upper")), "bb_lower": _f(row.get("bb_lower")),
               "ret_1d": _f(row.get("ret_1d")), "vol_20": _f(row.get("vol_20"))}
        ops.append(UpdateOne({"symbol": symbol, "timestamp": ts},
                             {"$set": doc}, upsert=True))
    if ops:
        out_col.bulk_write(ops, ordered=False)
    return len(ops)


def _f(v):
    try:
        f = float(v)
        return f if f == f else None  # NaN -> None
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=ALL_SYMBOLS)
    ap.add_argument("--mongo-uri", default=MONGO_URI)
    args = ap.parse_args()

    db = MongoClient(args.mongo_uri)[DB_NAME]
    prices, out = db["historical_prices"], db["technical_indicators"]
    out.create_index([("symbol", 1), ("timestamp", 1)], unique=True)
    for symbol in args.symbols:
        n = compute_for_symbol(prices, out, symbol)
        print(f"{symbol}: wrote {n} indicator rows")


if __name__ == "__main__":
    main()
