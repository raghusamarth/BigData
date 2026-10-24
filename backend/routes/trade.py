"""Trading: fixed ObjectId bug, added sell + holdings tracking."""
from fastapi import APIRouter, HTTPException
from database import users_collection, stocks_collection, historical_prices_collection, transactions_collection
from models import Trade
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/trade", tags=["Trading"])


def _oid(user_id: str) -> ObjectId:
    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")


def _latest_price(symbol: str) -> float:
    try:
        doc = historical_prices_collection.find_one({"symbol": symbol}, sort=[("timestamp", -1)])
        if doc:
            return float(doc["close"])
    except Exception:
        pass
    doc = stocks_collection.find_one({"symbol": symbol}, sort=[("date", -1)])
    if not doc:
        raise HTTPException(status_code=404, detail="Stock not found")
    return float(doc["close"])


def _apply_holding(holdings: list, symbol: str, qty_delta: int) -> list:
    holdings = holdings or []
    for h in holdings:
        if h.get("symbol") == symbol:
            h["quantity"] = h.get("quantity", 0) + qty_delta
            break
    else:
        if qty_delta > 0:
            holdings.append({"symbol": symbol, "quantity": qty_delta})
        else:
            raise HTTPException(status_code=400, detail="No holdings to sell")
    holdings = [h for h in holdings if h["quantity"] > 0]
    # validate no negative
    return holdings


@router.post("/buy")
def buy_stock(trade: Trade):
    oid = _oid(trade.user_id)
    price = _latest_price(trade.stock_symbol)
    user = users_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    total = price * trade.quantity
    if user.get("balance", 0) < total:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    new_holdings = _apply_holding(user.get("holdings", []), trade.stock_symbol, trade.quantity)
    users_collection.update_one({"_id": oid}, {"$inc": {"balance": -total}, "$set": {"holdings": new_holdings}})
    transactions_collection.insert_one({
        "user_id": oid, "stock_symbol": trade.stock_symbol, "quantity": trade.quantity,
        "price": price, "type": "buy", "timestamp": datetime.utcnow(),
    })
    return {"message": "Purchase successful", "price": price, "total": total}


@router.post("/sell")
def sell_stock(trade: Trade):
    oid = _oid(trade.user_id)
    price = _latest_price(trade.stock_symbol)
    user = users_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # check holding qty
    qty = next((h.get("quantity", 0) for h in user.get("holdings", []) if h.get("symbol") == trade.stock_symbol), 0)
    if qty < trade.quantity:
        raise HTTPException(status_code=400, detail="Insufficient holdings")
    new_holdings = _apply_holding(user.get("holdings", []), trade.stock_symbol, -trade.quantity)
    total = price * trade.quantity
    users_collection.update_one({"_id": oid}, {"$inc": {"balance": total}, "$set": {"holdings": new_holdings}})
    transactions_collection.insert_one({
        "user_id": oid, "stock_symbol": trade.stock_symbol, "quantity": trade.quantity,
        "price": price, "type": "sell", "timestamp": datetime.utcnow(),
    })
    return {"message": "Sale successful", "price": price, "total": total}


@router.get("/history/{user_id}")
def trade_history(user_id: str, limit: int = 100):
    oid = _oid(user_id)
    docs = list(transactions_collection.find({"user_id": oid}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    for d in docs:
        ts = d.get("timestamp")
        if hasattr(ts, "isoformat"):
            d["timestamp"] = ts.isoformat()
    return docs
