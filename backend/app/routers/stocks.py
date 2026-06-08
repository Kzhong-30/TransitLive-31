from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from app.core.models import (
    StockInfo, StockQuote, KlineData, OrderBook, KlineInterval,
    Alert, AlertCreate
)
from app.services.stock_service import stock_service

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=List[StockInfo], summary="获取所有支持的股票列表")
async def get_stocks():
    """获取系统支持的所有股票的基本信息列表"""
    return stock_service.get_all_stocks()


@router.get("/{symbol}/quote", response_model=StockQuote, summary="获取股票实时行情")
async def get_stock_quote(symbol: str):
    """
    获取指定股票的实时行情数据
    - **symbol**: 股票代码，如 AAPL, 600519
    """
    if not stock_service.get_stock_info(symbol):
        raise HTTPException(status_code=404, detail=f"股票代码 {symbol} 不存在")
    return await stock_service.get_current_quote(symbol)


@router.get("/{symbol}/history", response_model=List[KlineData], summary="获取历史K线数据")
async def get_kline_history(
    symbol: str,
    interval: KlineInterval = Query(default=KlineInterval.DAY, description="K线周期: 1m=分钟, 1d=日, 1w=周, 1M=月"),
    limit: int = Query(default=200, ge=1, le=500, description="返回数据条数")
):
    """
    获取指定股票的历史K线（OHLCV）数据

    - **symbol**: 股票代码
    - **interval**: K线周期
        - `1m`: 分钟级别K线
        - `1d`: 日K线（默认）
        - `1w`: 周K线
        - `1M`: 月K线
    - **limit**: 返回数据条数上限，默认200，最大500
    """
    if not stock_service.get_stock_info(symbol):
        raise HTTPException(status_code=404, detail=f"股票代码 {symbol} 不存在")
    return stock_service.generate_kline_history(symbol, interval, limit)


@router.get("/{symbol}/depth", response_model=OrderBook, summary="获取买卖五档盘口")
async def get_order_book(symbol: str):
    """
    获取指定股票的买卖五档盘口数据

    - **symbol**: 股票代码
    - 返回 bids（买盘）和 asks（卖盘）各五档价格和数量
    """
    if not stock_service.get_stock_info(symbol):
        raise HTTPException(status_code=404, detail=f"股票代码 {symbol} 不存在")
    return stock_service.generate_order_book(symbol)
