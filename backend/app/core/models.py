from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class KlineInterval(str, Enum):
    MINUTE = "1m"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1M"


class StockBase(BaseModel):
    symbol: str
    name: str
    sector: str


class StockInfo(StockBase):
    base_price: float


class StockQuote(BaseModel):
    symbol: str
    price: float
    open: float
    high: float
    low: float
    volume: int
    change: float
    change_percent: float
    timestamp: str


class KlineData(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class OrderBookLevel(BaseModel):
    price: float
    quantity: int


class OrderBook(BaseModel):
    symbol: str
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: str


class AlertCondition(str, Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"


class AlertCreate(BaseModel):
    symbol: str
    condition: AlertCondition
    target_price: float = Field(..., gt=0, description="目标价格")
    user_id: str = Field(..., description="用户标识")
    note: Optional[str] = None


class Alert(BaseModel):
    id: str
    symbol: str
    condition: AlertCondition
    target_price: float
    user_id: str
    note: Optional[str] = None
    created_at: str
    triggered: bool = False


class AlertNotification(BaseModel):
    type: str = "alert"
    alert_id: str
    symbol: str
    condition: str
    target_price: float
    current_price: float
    note: Optional[str] = None
    timestamp: str


class SubscribeMessage(BaseModel):
    type: str = "subscribe"
    symbols: List[str]


class UnsubscribeMessage(BaseModel):
    type: str = "unsubscribe"
    symbols: List[str]
