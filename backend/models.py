from pydantic import BaseModel, Field
from typing import Optional, List


class User(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str
    balance: float
    holdings: list = []


class Stock(BaseModel):
    """Legacy flat stock doc (kept for compat with old /stocks writes)."""
    symbol: str
    date: str
    open: float = Field(alias="open")
    close: float
    high: float
    low: float
    volume: int

    class Config:
        populate_by_name = True


class Trade(BaseModel):
    user_id: str
    stock_symbol: str
    quantity: int = Field(gt=0)


class PriceBar(BaseModel):
    symbol: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    interval: str = "1d"


class StockMetaIn(BaseModel):
    """Manager-mode stock registry entry."""
    symbol: str
    sector: str = "Unknown"
    exchange: str = "Unknown"
