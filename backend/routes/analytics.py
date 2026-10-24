"""Big Data analytics API: Mongo aggregation + cached Spark results."""
from fastapi import APIRouter, Query
from datetime import datetime
from database import historical_prices_collection, analytics_collection
from analytics.mongo_aggregations import (
    monthly_performance, top_gainers, sector_performance,
    volatility_ranking, volume_spikes,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _ser(docs):
    out = []
    for d in docs:
        d = dict(d)
        for k, v in list(d.items()):
            if hasattr(v, "isoformat"):
                d[k] = v.isoformat()
        out.append(d)
    return out


@router.get("/monthly/{symbol}")
def monthly(symbol: str, limit: int = 24):
    try:
        return _ser(list(historical_prices_collection.aggregate(monthly_performance(symbol, limit))))
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/top-gainers")
def top_gainers_api(start: str, end: str, limit: int = 10):
    try:
        s, e = datetime.fromisoformat(start), datetime.fromisoformat(end)
        return _ser(list(historical_prices_collection.aggregate(top_gainers(s, e, limit))))
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/sectors")
def sectors():
    try:
        return _ser(list(historical_prices_collection.aggregate(sector_performance())))
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/volatility")
def volatility(limit: int = 10):
    try:
        return _ser(list(historical_prices_collection.aggregate(volatility_ranking(limit))))
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/volume-spikes/{symbol}")
def spikes(symbol: str, mult: float = 3.0):
    try:
        return _ser(list(historical_prices_collection.aggregate(volume_spikes(symbol, mult))))
    except Exception as e:
        return {"error": str(e), "data": []}


@router.get("/correlation")
def correlation():
    """Latest Spark correlation job output (from analytics_results)."""
    try:
        doc = analytics_collection.find_one({"type": "correlation"}, sort=[("computedAt", -1)], projection={"_id": 0})
        return doc or {"message": "No correlation job run yet. Run jobs/spark_correlation.py"}
    except Exception as e:
        return {"error": str(e)}


@router.get("/anomalies")
def anomalies(limit: int = Query(50, le=500)):
    try:
        doc = analytics_collection.find_one({"type": "anomaly"}, sort=[("computedAt", -1)], projection={"_id": 0})
        if doc and isinstance(doc.get("payload"), list):
            return doc["payload"][:limit]
        return doc or {"message": "No anomaly job run yet."}
    except Exception as e:
        return {"error": str(e)}
