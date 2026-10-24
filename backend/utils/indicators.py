"""Pure pandas+numpy technical indicators (no TA-Lib needed)."""
import numpy as np
import pandas as pd


def sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()


def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100 - (100 / (1 + rs))
    # Flat series -> 0 handled by fillna; all-gains (loss=0) -> 100.
    out = out.mask((avg_loss == 0) & (avg_gain > 0), 100.0)
    return out.fillna(0)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def bollinger(close: pd.Series, n: int = 20, k: float = 2.0):
    mid = close.rolling(n).mean()
    std = close.rolling(n).std()
    return mid + k * std, mid, mid - k * std


def daily_returns(close: pd.Series) -> pd.Series:
    return close.pct_change()


def volatility(returns: pd.Series, n: int = 20) -> pd.Series:
    return returns.rolling(n).std()


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add sma20, sma50, ema12, ema26, rsi14, macd, macd_signal,
    bb_upper, bb_lower, ret_1d, vol_20. Requires Close column."""
    df = df.copy()
    close = df["Close"]
    df["sma20"] = sma(close, 20)
    df["sma50"] = sma(close, 50)
    df["ema12"] = ema(close, 12)
    df["ema26"] = ema(close, 26)
    df["rsi14"] = rsi(close, 14)
    m, s, _ = macd(close)
    df["macd"] = m
    df["macd_signal"] = s
    upper, _, lower = bollinger(close, 20)
    df["bb_upper"] = upper
    df["bb_lower"] = lower
    df["ret_1d"] = daily_returns(close)
    df["vol_20"] = volatility(df["ret_1d"], 20)
    return df
