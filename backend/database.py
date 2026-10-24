"""MongoDB connection + collection handles + index setup.

Collections:
  users, stocks (legacy compat), transactions (existing app)
  stocks_meta, historical_prices (time-series), technical_indicators,
  company_fundamentals, analytics_results (BDA upgrade)
"""
import os
from pymongo import MongoClient, ASCENDING, DESCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "stock_analysis_db")

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]

# Existing collections (preserved)
users_collection = db["users"]
stocks_collection = db["stocks"]  # legacy flat store, kept for compat
transactions_collection = db["transactions"]

# BDA collections
stocks_meta_collection = db["stocks_meta"]
historical_prices_collection = db["historical_prices"]
indicators_collection = db["technical_indicators"]
fundamentals_collection = db["company_fundamentals"]
analytics_collection = db["analytics_results"]


def ensure_time_series_collection():
    """Create historical_prices as a time-series collection if missing.

    Falls back to a regular collection on older Mongo versions.
    Safe to call on every startup (idempotent).
    """
    if "historical_prices" in db.list_collection_names():
        return
    try:
        db.create_collection(
            "historical_prices",
            timeseries={"timeField": "timestamp", "metaField": "symbol", "granularity": "hours"},
        )
    except Exception:
        # Old server or already exists as regular collection
        try:
            db.create_collection("historical_prices")
        except Exception:
            pass


def ensure_indexes():
    """Create indexes justifying each query pattern. Idempotent."""
    users_collection.create_index("username", unique=True)
    stocks_collection.create_index([("symbol", ASCENDING), ("date", DESCENDING)])
    transactions_collection.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
    stocks_meta_collection.create_index("symbol", unique=True)
    stocks_meta_collection.create_index("sector")
    # NOTE: unique indexes are NOT supported on time-series collections,
    # so historical_prices uses a plain compound index; dedupe is enforced
    # by the ingest upsert filter on (symbol, timestamp).
    historical_prices_collection.create_index([("symbol", ASCENDING), ("timestamp", ASCENDING)])
    indicators_collection.create_index([("symbol", ASCENDING), ("timestamp", ASCENDING)], unique=True)
    fundamentals_collection.create_index("symbol", unique=True)
    analytics_collection.create_index([("type", ASCENDING), ("computedAt", DESCENDING)])


def get_db():
    return db
