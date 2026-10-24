"""Manager mode: user removal, stock registry add/remove, manual bar entry,
dynamic custom fields (add/drop columns) + live schema inspection."""
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException
from bson import ObjectId
from database import (
    users_collection, transactions_collection, stocks_meta_collection,
    historical_prices_collection, indicators_collection, fundamentals_collection,
)
from models import PriceBar, StockMetaIn

router = APIRouter(prefix="/admin", tags=["Manager"])

FIELDABLE = {
    "users": users_collection,
    "stocks_meta": stocks_meta_collection,
    "company_fundamentals": fundamentals_collection,
    "historical_prices": historical_prices_collection,
    "technical_indicators": indicators_collection,
}

# Fields the app depends on — dropping these is refused.
CORE_FIELDS = {
    "users": {"_id", "username", "password", "balance", "holdings"},
    "stocks_meta": {"_id", "symbol", "sector", "exchange"},
    "company_fundamentals": {"_id", "symbol"},
    "historical_prices": {"_id", "timestamp", "symbol", "open", "high",
                          "low", "close", "volume", "interval", "source"},
    "technical_indicators": {"_id", "symbol", "timestamp"},
}

_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def _oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")


# ---- users ----
@router.get("/users")
def list_users():
    out = []
    for u in users_collection.find({}, {"password": 0}).sort("username", 1):
        u["user_id"] = str(u.pop("_id"))
        out.append(u)
    return out


@router.delete("/users/{user_id}")
def delete_user(user_id: str):
    oid = _oid(user_id)
    res = users_collection.delete_one({"_id": oid})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    tx = transactions_collection.delete_many({"user_id": oid}).deleted_count
    return {"message": "User removed", "transactions_removed": tx}


# ---- stock registry ----
@router.get("/stocks")
def list_stocks():
    return list(stocks_meta_collection.find({}, {"_id": 0}).sort("symbol", 1))


@router.post("/stocks")
def upsert_stock(meta: StockMetaIn):
    symbol = (meta.symbol or "").strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")
    stocks_meta_collection.update_one(
        {"symbol": symbol},
        {"$set": {"symbol": symbol, "sector": meta.sector or "Unknown",
                  "exchange": meta.exchange or "Unknown"}},
        upsert=True,
    )
    return {"message": "Stock registered", "symbol": symbol}


@router.delete("/stocks/{symbol}")
def delete_stock(symbol: str, purge: bool = True):
    symbol = (symbol or "").strip().upper()
    meta = stocks_meta_collection.delete_one({"symbol": symbol}).deleted_count
    bars, ind = 0, 0
    if purge:
        bars = historical_prices_collection.delete_many({"symbol": symbol}).deleted_count
        ind = indicators_collection.delete_many({"symbol": symbol}).deleted_count
    if meta == 0 and bars == 0:
        raise HTTPException(status_code=404, detail="Stock not found")
    return {"message": "Stock removed", "symbol": symbol,
            "price_bars_removed": bars, "indicator_rows_removed": ind}


# ---- manual price bar ----
@router.post("/bars")
def add_bar(bar: PriceBar):
    symbol = (bar.symbol or "").strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")
    try:
        ts = datetime.fromisoformat(bar.timestamp)
    except Exception:
        raise HTTPException(status_code=400, detail="timestamp must be ISO, e.g. 2026-10-07 or 2026-10-07T10:30:00")
    if bar.high < bar.low:
        raise HTTPException(status_code=400, detail="high cannot be below low")
    if not (bar.low <= bar.open <= bar.high and bar.low <= bar.close <= bar.high):
        raise HTTPException(status_code=400, detail="open/close must sit inside [low, high]")
    if bar.volume < 0:
        raise HTTPException(status_code=400, detail="volume cannot be negative")
    if historical_prices_collection.find_one(
            {"symbol": symbol, "timestamp": ts, "interval": bar.interval}):
        raise HTTPException(status_code=409, detail="Bar already exists for symbol+timestamp+interval")
    historical_prices_collection.insert_one({
        "symbol": symbol, "timestamp": ts, "open": bar.open, "high": bar.high,
        "low": bar.low, "close": bar.close, "volume": bar.volume,
        "interval": bar.interval, "source": "manual-entry",
    })
    if not stocks_meta_collection.find_one({"symbol": symbol}):
        stocks_meta_collection.insert_one({"symbol": symbol, "sector": "Unknown", "exchange": "Manual"})
    return {"message": "Bar recorded", "symbol": symbol, "timestamp": ts.isoformat()}


# ---- dynamic custom fields (add/drop columns) ----
def _coll(name: str):
    if name not in FIELDABLE:
        raise HTTPException(status_code=400,
                            detail=f"Collection must be one of {sorted(FIELDABLE)}")
    return FIELDABLE[name]


def _check_name(collection: str, name: str) -> str:
    name = (name or "").strip()
    if not _NAME_RE.match(name):
        raise HTTPException(status_code=400,
                            detail="Field name must start with a letter, letters/digits/_ only, max 64 chars")
    if name in CORE_FIELDS[collection]:
        raise HTTPException(status_code=400,
                            detail=f"'{name}' is a core field of {collection} and is protected")
    return name


def _cast(dtype: str, value: str):
    try:
        if dtype == "float":
            return float(value)
        if dtype == "int":
            return int(value)
        if dtype == "bool":
            return str(value).strip().lower() in ("true", "1", "yes")
        return str(value)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Default '{value}' is not a valid {dtype}")


@router.get("/schema")
def get_schema(collection: str, sample: int = 200):
    """Live schema: union of field names over a $sample of docs + doc count."""
    coll = _coll(collection)
    sample = max(1, min(sample, 1000))
    docs = list(coll.aggregate([{"$sample": {"size": sample}}]))
    seen = {}
    for d in docs:
        for k, v in d.items():
            info = seen.setdefault(k, {"types": set(), "present": 0})
            info["types"].add(type(v).__name__)
            info["present"] += 1
    fields = [{"name": k, "types": sorted(v["types"]), "present": v["present"],
               "core": k in CORE_FIELDS[collection]} for k, v in seen.items()]
    fields.sort(key=lambda f: (f["core"], f["name"]))
    return {"collection": collection, "sampled": len(docs),
            "total_docs": coll.estimated_document_count(), "fields": fields}


@router.post("/fields")
def add_field(collection: str, name: str, dtype: str = "str",
              default: str = "", backfill: bool = True):
    """Add a column: every future doc can carry it; backfill $sets it on all existing docs."""
    coll = _coll(collection)
    name = _check_name(collection, name)
    if dtype not in ("str", "float", "int", "bool"):
        raise HTTPException(status_code=400, detail="dtype must be str|float|int|bool")
    value = _cast(dtype, default)
    modified = 0
    if backfill:
        # Multi-update is allowed on time-series collections (only single-doc
        # upserts and time/meta-field rewrites are rejected).
        modified = coll.update_many({}, {"$set": {name: value}}).modified_count
    return {"message": "Field added", "collection": collection, "name": name,
            "dtype": dtype, "default": value, "backfilled_docs": modified}


@router.delete("/fields")
def drop_field(collection: str, name: str):
    """Drop a column: $unset removes it from every doc that has it."""
    coll = _coll(collection)
    name = _check_name(collection, name)
    modified = coll.update_many({}, {"$unset": {name: ""}}).modified_count
    return {"message": "Field dropped", "collection": collection, "name": name,
            "modified_docs": modified}
