"""Validation helpers: clean raw OHLCV frames and convert to Mongo docs."""
from datetime import datetime

import pandas as pd


def clean_ohlcv(df: pd.DataFrame):
    """Clean a raw yfinance OHLCV DataFrame.

    Returns (clean_df, report) where report counts dropped rows per rule.
    """
    report = {"input_rows": 0 if df is None else len(df), "dropped_na": 0,
              "dropped_bad_range": 0, "dropped_neg_volume": 0,
              "dropped_duplicates": 0, "output_rows": 0}
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame(), report

    df = df.copy()

    # Normalise column names (yfinance may return MultiIndex).
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df.columns = [str(c).strip().capitalize() for c in df.columns]
    # 'Adj Close' -> keep, map common variants
    rename = {"Adj close": "Adj_Close", "Adj_close": "Adj_Close"}
    df.columns = [rename.get(c, c) for c in df.columns]

    before = len(df)
    df = df.dropna(subset=[c for c in ["Open", "High", "Low", "Close"] if c in df.columns])
    report["dropped_na"] = before - len(df)

    if {"High", "Low"}.issubset(df.columns):
        before = len(df)
        df = df[df["High"] >= df["Low"]]
        report["dropped_bad_range"] = before - len(df)

    if "Volume" in df.columns:
        before = len(df)
        df = df[df["Volume"] >= 0]
        report["dropped_neg_volume"] = before - len(df)
    else:
        df["Volume"] = 0

    # Deduplicate on index (timestamp).
    before = len(df)
    df = df[~df.index.duplicated(keep="last")]
    report["dropped_duplicates"] = before - len(df)
    df = df.sort_index()

    report["output_rows"] = len(df)
    return df, report


def to_documents(symbol, df: pd.DataFrame, interval="1d", source="yfinance"):
    """Convert OHLCV DataFrame to list of Mongo-ready dicts.

    Expected columns: Open/High/Low/Close/Volume, DatetimeIndex.
    """
    docs = []
    if df is None or df.empty:
        return docs
    for ts, row in df.iterrows():
        # Normalise timestamp to python datetime.
        if isinstance(ts, pd.Timestamp):
            ts_py = ts.to_pydatetime()
        elif isinstance(ts, datetime):
            ts_py = ts
        else:
            ts_py = pd.to_datetime(ts).to_pydatetime()
        docs.append({
            "symbol": symbol,
            "timestamp": ts_py,
            "open": float(row.get("Open", 0) or 0),
            "high": float(row.get("High", 0) or 0),
            "low": float(row.get("Low", 0) or 0),
            "close": float(row.get("Close", 0) or 0),
            "volume": int(row.get("Volume", 0) or 0),
            "interval": interval,
            "source": source,
        })
    return docs


def validate_doc(doc: dict) -> bool:
    """Return True if a price doc looks sane."""
    try:
        if doc["high"] < doc["low"]:
            return False
        # Allow tiny floating point tolerance outside [low, high].
        tol = 1e-6
        if not (doc["low"] - tol <= doc["close"] <= doc["high"] + tol):
            return False
        if doc["volume"] < 0:
            return False
        if doc["open"] < 0 or doc["close"] < 0:
            return False
        return True
    except (KeyError, TypeError):
        return False
