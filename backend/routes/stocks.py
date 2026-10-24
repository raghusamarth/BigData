"""Stock reads: legacy `stocks` + Big Data `historical_prices` (time-series)."""
from fastapi import APIRouter, Query
from database import stocks_collection, historical_prices_collection

router = APIRouter(prefix="/stocks", tags=["Stocks"])


@router.get("/")
def get_all_stocks(limit: int = Query(100, le=1000)):
    """Legacy endpoint (kept). Reads old flat `stocks` collection."""
    return list(stocks_collection.find({}, {"_id": 0}).limit(limit))


@router.get("/{symbol}")
def get_stock(symbol: str, limit: int = Query(30, le=500)):
    """Legacy per-symbol lookup, now prefers time-series data with fallback."""
    try:
        docs = list(historical_prices_collection.find(
            {"symbol": symbol}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        if docs:
            for d in docs:
                ts = d.get("timestamp")
                if hasattr(ts, "isoformat"):
                    d["timestamp"] = ts.isoformat()
            return docs
    except Exception:
        pass
    return list(stocks_collection.find({"symbol": symbol}, {"_id": 0}).sort("date", -1).limit(limit))


@router.get("/{symbol}/history")
def get_history(symbol: str, interval: str = "1d", limit: int = Query(500, le=5000)):
    q = {"symbol": symbol}
    if interval != "all":
        q["interval"] = interval
    try:
        docs = list(historical_prices_collection.find(q, {"_id": 0}).sort("timestamp", 1).limit(limit))
        for d in docs:
            ts = d.get("timestamp")
            if hasattr(ts, "isoformat"):
                d["timestamp"] = ts.isoformat()
        return {"symbol": symbol, "count": len(docs), "data": docs}
    except Exception as e:
        return {"symbol": symbol, "count": 0, "data": [], "error": str(e)}
