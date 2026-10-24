"""Spark correlation job: cross-stock returns correlation + anomalies.

- Reads historical_prices via pymongo into pandas, then to Spark.
- Pivots to (date × symbol) returns matrix, computes MLlib correlation.
- Sector averages (via stocks_meta) + z-score anomalies.
- Writes JSON-serialisable results to analytics_results collection.

Usage:
    python -m jobs.spark_correlation --mongo-uri mongodb://localhost:27017
    python -m jobs.spark_correlation --pandas-only   # no pyspark needed

Falls back to pandas-only mode automatically if pyspark is missing.
"""
import argparse
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "stock_analysis_db"


def load_returns(mongo_uri):
    """Return (returns_pandas, sector_map)."""
    from pymongo import MongoClient
    import pandas as pd

    db = MongoClient(mongo_uri)[DB_NAME]
    # Daily bars only: keeps the O(n^2) job fast and methodologically clean
    # now that hourly synthetic bars exist alongside daily ones.
    rows = list(db["historical_prices"].find(
        {"interval": "1d"}, {"symbol": 1, "timestamp": 1, "close": 1}))
    if not rows:
        return pd.DataFrame(), {}
    df = pd.DataFrame(rows).dropna()
    px = df.pivot_table(index="timestamp", columns="symbol",
                        values="close", aggfunc="last").sort_index()
    rets = px.pct_change().dropna(how="all")
    meta = {m["symbol"]: m.get("sector", "Unknown")
            for m in db["stocks_meta"].find({}, {"symbol": 1, "sector": 1})}
    return rets, meta


def pandas_fallback(rets, meta):
    """Correlation + anomalies using only pandas (no Spark)."""
    corr = rets.corr().fillna(0)
    sector_avg = rets.copy()
    # Group columns by sector for sector-mean returns.
    inv = {}
    for sym, sec in meta.items():
        if sym in rets.columns:
            inv.setdefault(sec, []).append(sym)
    sector_rets = {s: rets[c].mean(axis=1) for s, c in inv.items() if c}
    z = (rets - rets.mean()) / rets.std().replace(0, float("nan"))
    anomalies = []
    stacked = z.stack()
    for (ts, sym), v in stacked.items():
        if abs(float(v)) > 3:
            anomalies.append({"timestamp": str(ts), "symbol": sym,
                              "z_score": round(float(v), 3)})
    return corr, sector_rets, anomalies[:500]


def spark_run(rets, spark):
    """MLlib correlation on the returns matrix. Returns nested list + symbols."""
    from pyspark.ml.feature import VectorAssembler
    from pyspark.ml.stat import Correlation
    import pandas as pd

    cols = list(rets.columns)
    pdf = rets.reset_index(drop=True).fillna(0)
    sdf = spark.createDataFrame(pdf[cols])
    assembler = VectorAssembler(inputCols=cols, outputCol="features")
    vec_df = assembler.transform(sdf).select("features")
    corr_mat = Correlation.corr(vec_df, "features").head()[0].toArray()
    return pd.DataFrame(corr_mat, index=cols, columns=cols).fillna(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mongo-uri", default=MONGO_URI)
    ap.add_argument("--pandas-only", action="store_true",
                    help="skip pyspark even if installed")
    args = ap.parse_args()

    rets, meta = load_returns(args.mongo_uri)
    if rets.empty:
        print("No price data found. Run ingest_bulk first.")
        return

    corr = None
    if not args.pandas_only:
        try:
            from pyspark.sql import SparkSession
            spark = (SparkSession.builder.master("local[*]")
                     .appName("stock-correlation").getOrCreate())
            spark.sparkContext.setLogLevel("WARN")
            corr = spark_run(rets, spark)
            print("Spark correlation OK:", corr.shape)
            spark.stop()
        except ImportError:
            print("pyspark not installed -> pandas-only fallback")
        except Exception as exc:
            print(f"Spark failed ({exc}) -> pandas-only fallback")

    if corr is None:
        corr, sector_rets, anomalies = pandas_fallback(rets, meta)
    else:
        _, sector_rets, anomalies = pandas_fallback(rets, meta)

    def str_keys(s):
        return {str(k)[:10]: round(float(v), 6) for k, v in s.dropna().tail(5).items()}

    from pymongo import MongoClient
    db = MongoClient(args.mongo_uri)[DB_NAME]
    now = datetime.utcnow()
    db["analytics_results"].insert_one({
        "type": "correlation", "job": "spark_correlation", "computedAt": now,
        "mode": "pandas" if args.pandas_only else "spark-or-pandas",
        "payload": {"symbols": list(rets.columns),
                    "correlation": corr.round(4).to_dict(),
                    "sector_avg_returns": {s: str_keys(v) for s, v in sector_rets.items()}},
    })
    db["analytics_results"].insert_one({
        "type": "anomaly", "job": "spark_correlation", "computedAt": now,
        "payload": anomalies,
    })
    print(f"Wrote analytics_results ({len(anomalies)} anomalies, "
          f"{len(rets.columns)} symbols)")


if __name__ == "__main__":
    main()
