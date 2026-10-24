"""Fetch OHLCV data from yfinance with cleaning + throttling.

Run-safe: no Mongo logic here, only fetching + cleaning.
"""
import time

import pandas as pd

try:
    from .validation import clean_ohlcv
except ImportError:  # run as plain script
    from utils.validation import clean_ohlcv


def fetch_symbol(symbol: str, period: str = "10y", interval: str = "1d"):
    """Fetch one symbol. Returns (df, report). Empty df on failure."""
    import yfinance as yf

    try:
        df = yf.download(symbol, period=period, interval=interval,
                         auto_adjust=False, progress=False)
        if df is None or len(df) == 0:
            return pd.DataFrame(), {"symbol": symbol, "error": "no data", "output_rows": 0}
        clean, report = clean_ohlcv(df)
        report["symbol"] = symbol
        return clean, report
    except Exception as exc:  # never crash a bulk run on one ticker
        return pd.DataFrame(), {"symbol": symbol, "error": str(exc), "output_rows": 0}


def fetch_bulk(symbols, period: str = "10y", interval: str = "1d", sleep: float = 0.5):
    """Fetch many symbols. Returns dict symbol -> (df, report)."""
    out = {}
    for sym in symbols:
        df, rep = fetch_symbol(sym, period=period, interval=interval)
        out[sym] = (df, rep)
        time.sleep(sleep)  # be polite to Yahoo
    return out
