"""Synthetic market seeder: fast Big Data bootstrap without yfinance.

Generates realistic OHLCV via geometric Brownian motion with a shared
market factor + sector drift/vol, volume with lognormal noise + spikes.
Every doc is labeled source="synthetic-gbm" so real vs synthetic stays
honest (veracity requirement). Existing real rows are never touched.

Scale (defaults): 30 symbols x 15y daily (~113k) + 30 x 8y hourly (~420k)
  -> ~530k price docs, ~1M total with indicators. Numpy does it in seconds.

Usage (inside api container):
    docker compose exec api python -m jobs.seed_synth
    docker compose exec api python -m jobs.seed_synth --years 10 --hourly-years 5 --seed 7
    docker compose exec api python -m jobs.seed_synth --wipe-synthetic   # idempotent re-run
"""
import argparse
import hashlib
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.symbols import ALL_SYMBOLS, EXCHANGE_MAP, SECTOR_MAP  # noqa: E402

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "stock_analysis_db"

SECTOR_DRIFT = {  # annualised drift per sector
    "Technology": 0.14, "IT": 0.12, "Semiconductors": 0.18, "Banking": 0.08,
    "Financial Services": 0.08, "Energy": 0.06, "Auto": 0.09, "Pharma": 0.10,
    "FMCG": 0.07, "Consumer": 0.08, "Retail": 0.09, "Media": 0.05,
    "E-Commerce": 0.13, "Infrastructure": 0.08, "Unknown": 0.08,
}
SECTOR_VOL = {  # annualised vol per sector
    "Technology": 0.32, "IT": 0.28, "Semiconductors": 0.45, "Banking": 0.30,
    "Financial Services": 0.26, "Energy": 0.34, "Auto": 0.38, "Pharma": 0.30,
    "FMCG": 0.22, "Consumer": 0.25, "Retail": 0.26, "Media": 0.36,
    "E-Commerce": 0.38, "Infrastructure": 0.28, "Unknown": 0.30,
}


def _start_price(symbol):
    h = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
    return 50 + (h % 2950)


def gen_symbol(symbol, trading_days, bars_per_day, seed):
    """Return list of OHLCV dicts (no timestamp yet)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    sector = SECTOR_MAP.get(symbol, "Unknown")
    mu, sig = SECTOR_DRIFT.get(sector, 0.08), SECTOR_VOL.get(sector, 0.30)
    n = len(trading_days) * bars_per_day
    dt = 1 / (252 * bars_per_day)

    market = rng.normal(0, 0.18 * np.sqrt(dt), n)          # shared market factor
    jumps = rng.random(n) < 0.002                          # crash/euphoria days
    market[jumps] += rng.choice([-1, 1], jumps.sum()) * rng.uniform(0.02, 0.06, jumps.sum())
    idio = rng.normal(0, sig * np.sqrt(dt), n)
    rets = mu * dt + 0.6 * market + idio

    closes = _start_price(symbol) * np.exp(np.cumsum(rets))
    prev = np.concatenate([[closes[0] / (1 + rets[0])], closes[:-1]])
    opens = prev * (1 + rng.normal(0, sig * np.sqrt(dt) * 0.4, n))
    span = np.abs(rng.normal(0, sig * np.sqrt(dt), n)) * closes + 1e-6
    highs = np.maximum(opens, closes) + span * rng.uniform(0.3, 1.0, n)
    lows = np.minimum(opens, closes) - span * rng.uniform(0.3, 1.0, n)
    lows = np.maximum(lows, 0.01)
    base_vol = 1e6 * (0.3 + (hash(seed) % 100) / 100)
    vols = (base_vol * np.exp(rng.normal(0, 0.5, n))).astype(int)
    spikes = rng.random(n) < 0.01
    vols[spikes] *= rng.integers(3, 8, spikes.sum())
    return opens, highs, lows, closes, vols


def run(symbols, years, hourly_years, seed, mongo_uri, batch, wipe):
    import pandas as pd
    from pymongo import MongoClient

    db = MongoClient(mongo_uri)[DB_NAME]
    prices, meta = db["historical_prices"], db["stocks_meta"]
    if wipe:
        r = prices.delete_many({"source": "synthetic-gbm"})
        print(f"wiped {r.deleted_count} old synthetic rows")

    for s in symbols:
        meta.update_one({"symbol": s},
                        {"$set": {"symbol": s, "sector": SECTOR_MAP.get(s, "Unknown"),
                                  "exchange": EXCHANGE_MAP.get(s, "Unknown")}},
                        upsert=True)

    end = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    total = 0

    def store(symbol, days, bars_per_day, interval, seed_off):
        nonlocal total
        opens, highs, lows, closes, vols = gen_symbol(symbol, days, bars_per_day, seed + seed_off)
        have = {d["timestamp"] for d in prices.find(
            {"symbol": symbol, "interval": interval, "source": "synthetic-gbm"},
            {"timestamp": 1, "_id": 0})}
        buf = []
        idx = 0
        for di, day in enumerate(days):
            for b in range(bars_per_day):
                ts = day if bars_per_day == 1 else day + timedelta(hours=9, minutes=30 + 60 * b)
                idx += 1
                if ts in have:
                    continue
                i = di * bars_per_day + b
                buf.append({"symbol": symbol, "timestamp": ts,
                            "open": round(float(opens[i]), 2), "high": round(float(highs[i]), 2),
                            "low": round(float(lows[i]), 2), "close": round(float(closes[i]), 2),
                            "volume": int(vols[i]), "interval": interval,
                            "source": "synthetic-gbm"})
                if len(buf) >= batch:
                    prices.insert_many(buf, ordered=False)
                    total += len(buf)
                    buf = []
        if buf:
            prices.insert_many(buf, ordered=False)
            total += len(buf)

    import pandas as pd  # noqa: F811
    for k, s in enumerate(symbols):
        daily_days = pd.bdate_range(end=end, periods=int(years * 252)).to_pydatetime().tolist()
        store(s, daily_days, 1, "1d", k * 1000)
        print(f"{s}: daily done ({years}y)")
    for k, s in enumerate(symbols):
        hdays = pd.bdate_range(end=end, periods=int(hourly_years * 252)).to_pydatetime().tolist()
        store(s, hdays, 7, "1h", k * 1000 + 77)
        print(f"{s}: hourly done ({hourly_years}y)")
    print(f"TOTAL synthetic rows inserted: {total}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="*", default=ALL_SYMBOLS)
    ap.add_argument("--years", type=float, default=15)
    ap.add_argument("--hourly-years", type=float, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mongo-uri", default=MONGO_URI)
    ap.add_argument("--batch", type=int, default=10000)
    ap.add_argument("--wipe-synthetic", action="store_true")
    a = ap.parse_args()
    run(a.symbols, a.years, a.hourly_years, a.seed, a.mongo_uri, a.batch, a.wipe_synthetic)


if __name__ == "__main__":
    main()
