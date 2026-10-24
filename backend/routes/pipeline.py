"""Pipeline health: counts, date ranges, ingestion rate, 5Vs evidence."""
from fastapi import APIRouter
from database import db
from analytics.mongo_aggregations import pipeline_stats

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])


@router.get("/stats")
def stats():
    try:
        per_symbol = list(db.historical_prices.aggregate(pipeline_stats()))
        total = sum(r.get("rows", 0) for r in per_symbol)
        symbols = len(per_symbol)
        for r in per_symbol:
            for k in ("min_date", "max_date"):
                if hasattr(r.get(k), "isoformat"):
                    r[k] = r[k].isoformat()
        ind = db.technical_indicators.count_documents({})
        jobs = list(db.analytics_results.find({}, {"_id": 0}).sort("computedAt", -1).limit(5))
        for j in jobs:
            if hasattr(j.get("computedAt"), "isoformat"):
                j["computedAt"] = j["computedAt"].isoformat()
        return {
            "total_price_docs": total, "symbols": symbols,
            "indicator_docs": ind, "per_symbol": per_symbol[:50],
            "recent_jobs": jobs,
            "collections": db.list_collection_names(),
        }
    except Exception as e:
        return {"error": str(e), "total_price_docs": 0}


@router.get("/diagram")
def diagram():
    return {"pipeline": "yfinance -> ingest(clean/validate) -> MongoDB time-series -> [Mongo Aggregation | PySpark] -> analytics_results -> FastAPI -> Streamlit"}
