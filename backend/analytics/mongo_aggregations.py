"""Mongo aggregation-pipeline builders.

Each function returns a *pipeline list* (not executed), targeting:
  - historical_prices: {symbol, timestamp, open, high, low, close, volume, ...}
  - stocks_meta:       {symbol, sector, exchange, ...}

Execute with:  db.historical_prices.aggregate(pipeline)
"""


def monthly_performance(symbol: str, limit: int = 24):
    """Avg close + total volume per calendar month for one symbol."""
    return [
        {"$match": {"symbol": symbol}},
        {"$group": {
            "_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}},
            "avg_close": {"$avg": "$close"},
            "total_volume": {"$sum": "$volume"},
            "days": {"$sum": 1},
        }},
        {"$project": {
            "_id": 0, "year": "$_id.year", "month": "$_id.month",
            "avg_close": 1, "total_volume": 1, "days": 1,
        }},
        {"$sort": {"year": -1, "month": -1}},
        {"$limit": limit},
    ]


def top_gainers(start, end, limit: int = 10):
    """Rank symbols by % return between start and end dates."""
    return [
        {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
        {"$sort": {"symbol": 1, "timestamp": 1}},
        {"$group": {
            "_id": "$symbol",
            "first_close": {"$first": "$close"},
            "last_close": {"$last": "$close"},
        }},
        {"$project": {
            "_id": 0, "symbol": "$_id", "first_close": 1, "last_close": 1,
            "pct_return": {"$multiply": [
                {"$divide": [{"$subtract": ["$last_close", "$first_close"]},
                             "$first_close"]}, 100]},
        }},
        {"$sort": {"pct_return": -1}},
        {"$limit": limit},
    ]


def sector_performance():
    """Avg daily return per sector (joins stocks_meta for sector)."""
    return [
        {"$lookup": {
            "from": "stocks_meta", "localField": "symbol",
            "foreignField": "symbol", "as": "meta",
        }},
        {"$unwind": "$meta"},
        {"$group": {
            "_id": "$meta.sector",
            "avg_close": {"$avg": "$close"},
            "total_volume": {"$sum": "$volume"},
            "symbols": {"$addToSet": "$symbol"},
        }},
        {"$project": {"_id": 0, "sector": "$_id", "avg_close": 1,
                      "total_volume": 1, "symbols": 1}},
        {"$sort": {"total_volume": -1}},
    ]


def volatility_ranking(limit: int = 10):
    """Rank symbols by std-dev of close (simple volatility proxy)."""
    return [
        {"$group": {
            "_id": "$symbol",
            "std_close": {"$stdDevPop": "$close"},
            "avg_close": {"$avg": "$close"},
            "days": {"$sum": 1},
        }},
        {"$project": {
            "_id": 0, "symbol": "$_id", "std_close": 1, "avg_close": 1, "days": 1,
            "coef_var": {"$divide": ["$std_close", "$avg_close"]},
        }},
        {"$sort": {"coef_var": -1}},
        {"$limit": limit},
    ]


def volume_spikes(symbol: str, mult: float = 3.0, limit: int = 20):
    """Days where volume exceeded mult × average volume for the symbol."""
    return [
        {"$match": {"symbol": symbol}},
        {"$group": {
            "_id": "$symbol", "avg_vol": {"$avg": "$volume"},
            "docs": {"$push": "$$ROOT"},
        }},
        {"$unwind": "$docs"},
        {"$match": {"$expr": {"$gt": ["$docs.volume",
                                     {"$multiply": [mult, "$avg_vol"]}]}}},
        {"$project": {"_id": 0, "symbol": "$docs.symbol",
                      "timestamp": "$docs.timestamp", "close": "$docs.close",
                      "volume": "$docs.volume", "avg_vol": "$avg_vol"}},
        {"$sort": {"volume": -1}},
        {"$limit": limit},
    ]


def pipeline_stats():
    """Row counts + date range per symbol (ingestion health check)."""
    return [
        {"$group": {
            "_id": "$symbol",
            "rows": {"$sum": 1},
            "min_date": {"$min": "$timestamp"},
            "max_date": {"$max": "$timestamp"},
        }},
        {"$project": {"_id": 0, "symbol": "$_id", "rows": 1,
                      "min_date": 1, "max_date": 1}},
        {"$sort": {"rows": -1}},
    ]
