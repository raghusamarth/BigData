"""
Symbol universe for the Big Data demo.

30 symbols total (15 NSE + 15 US) so the pipeline stays
student-runnable on a laptop (10y daily ≈ 75k rows).

To extend to 150 (NIFTY 50 + S&P 100):
    1. Add the remaining tickers to NIFTY_50 / SP_100_SUBSET below.
    2. Add matching entries in SECTOR_MAP and EXCHANGE_MAP.
    3. Re-run:  python -m jobs.ingest_bulk --period 10y
"""

# ~15 NSE symbols (yfinance needs the .NS suffix)
NIFTY_50 = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "TATAMOTORS.NS",
    "TITAN.NS",
    "ITC.NS",
    "LT.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "SUNPHARMA.NS",
    "MARUTI.NS",
    "ONGC.NS",
]

# ~15 US symbols (S&P-100 subset)
SP_100_SUBSET = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "TSLA",
    "META",
    "NVDA",
    "JPM",
    "JNJ",
    "V",
    "PG",
    "XOM",
    "WMT",
    "DIS",
    "NFLX",
]

ALL_SYMBOLS = NIFTY_50 + SP_100_SUBSET

SECTOR_MAP = {
    # India
    "RELIANCE.NS": "Energy",
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "HDFCBANK.NS": "Banking",
    "ICICIBANK.NS": "Banking",
    "SBIN.NS": "Banking",
    "TATAMOTORS.NS": "Auto",
    "TITAN.NS": "Consumer",
    "ITC.NS": "FMCG",
    "LT.NS": "Infrastructure",
    "AXISBANK.NS": "Banking",
    "KOTAKBANK.NS": "Banking",
    "SUNPHARMA.NS": "Pharma",
    "MARUTI.NS": "Auto",
    "ONGC.NS": "Energy",
    # US
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "AMZN": "E-Commerce",
    "TSLA": "Auto",
    "META": "Technology",
    "NVDA": "Semiconductors",
    "JPM": "Banking",
    "JNJ": "Pharma",
    "V": "Financial Services",
    "PG": "FMCG",
    "XOM": "Energy",
    "WMT": "Retail",
    "DIS": "Media",
    "NFLX": "Media",
}

EXCHANGE_MAP = {s: ("NSE" if s.endswith(".NS") else "NASDAQ/NYSE") for s in ALL_SYMBOLS}
