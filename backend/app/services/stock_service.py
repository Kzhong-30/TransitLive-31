import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from typing import Self
import logging

from app.core.models import (
    StockInfo, StockQuote, KlineData, OrderBook, OrderBookLevel,
    KlineInterval, Alert, AlertNotification
)
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


STOCKS_DATA: List[StockInfo] = [
    StockInfo(symbol="AAPL", name="Apple Inc.", sector="Technology", base_price=178.50),
    StockInfo(symbol="GOOGL", name="Alphabet Inc.", sector="Technology", base_price=141.25),
    StockInfo(symbol="MSFT", name="Microsoft Corp.", sector="Technology", base_price=378.90),
    StockInfo(symbol="AMZN", name="Amazon.com Inc.", sector="Consumer", base_price=178.35),
    StockInfo(symbol="TSLA", name="Tesla Inc.", sector="Automotive", base_price=248.75),
    StockInfo(symbol="NVDA", name="NVIDIA Corp.", sector="Semiconductors", base_price=875.60),
    StockInfo(symbol="META", name="Meta Platforms Inc.", sector="Technology", base_price=505.10),
    StockInfo(symbol="JPM", name="JPMorgan Chase & Co.", sector="Financials", base_price=198.25),
    StockInfo(symbol="V", name="Visa Inc.", sector="Financials", base_price=278.40),
    StockInfo(symbol="JNJ", name="Johnson & Johnson", sector="Healthcare", base_price=158.65),
    StockInfo(symbol="600519", name="贵州茅台", sector="消费", base_price=1680.00),
    StockInfo(symbol="000858", name="五粮液", sector="消费", base_price=148.50),
    StockInfo(symbol="601318", name="中国平安", sector="金融", base_price=48.75),
    StockInfo(symbol="000001", name="平安银行", sector="金融", base_price=11.85),
    StockInfo(symbol="600036", name="招商银行", sector="金融", base_price=35.20),
]


class StockDataService:
    _instance: Optional[Self] = None
    _stock_state: Dict[str, Dict] = {}
    _alerts: Dict[str, Alert] = {}
    _alert_callbacks = []

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_stock_state()
        return cls._instance

    def _init_stock_state(self) -> None:
        for stock in STOCKS_DATA:
            base = stock.base_price
            volatility = 0.005
            self._stock_state[stock.symbol] = {
                "base_price": base,
                "current_price": base,
                "open_price": base,
                "high_price": base,
                "low_price": base,
                "prev_close": base * random.uniform(0.98, 1.02),
                "volume": random.randint(1000000, 5000000),
                "volatility": volatility,
            }
        self._alerts = {}

    async def _load_from_redis(self) -> None:
        errors: List[Exception] = []
        for stock in STOCKS_DATA:
            try:
                key = f"stock:state:{stock.symbol}"
                state = await redis_client.get_json(key)
                if state:
                    self._stock_state[stock.symbol] = state
            except Exception as e:
                errors.append(RuntimeError(f"load state {stock.symbol}: {e}"))
        try:
            alerts_data = await redis_client.hgetall_json("stock:alerts")
            for k, v in alerts_data.items():
                self._alerts[k] = Alert(**v)
        except Exception as e:
            errors.append(RuntimeError(f"load alerts: {e}"))
        if errors:
            try:
                raise ExceptionGroup("Redis load errors", errors)
            except ExceptionGroup as eg:
                logger.warning("_load_from_redis had %d sub-errors", len(eg.exceptions))

    async def _save_to_redis(self) -> None:
        errors: List[Exception] = []
        for symbol, state in self._stock_state.items():
            try:
                await redis_client.set_json(f"stock:state:{symbol}", state, ex=3600)
            except Exception as e:
                errors.append(RuntimeError(f"save state {symbol}: {e}"))
        for alert_id, alert in self._alerts.items():
            try:
                await redis_client.hset_json("stock:alerts", alert_id, alert.model_dump())
            except Exception as e:
                errors.append(RuntimeError(f"save alert {alert_id}: {e}"))
        if errors:
            try:
                raise ExceptionGroup("Redis save errors", errors)
            except ExceptionGroup as eg:
                logger.warning("_save_to_redis had %d sub-errors", len(eg.exceptions))

    def get_all_stocks(self) -> List[StockInfo]:
        return STOCKS_DATA

    def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        for s in STOCKS_DATA:
            if s.symbol == symbol:
                return s
        return None

    def _random_walk(self, current: float, volatility: float) -> float:
        change = random.gauss(0, 1) * volatility * current
        new_price = current + change
        return max(0.01, new_price)

    async def generate_quote(self, symbol: str) -> StockQuote:
        state = self._stock_state.get(symbol)
        if not state:
            raise ValueError(f"Unknown stock symbol: {symbol}")

        new_price = self._random_walk(state["current_price"], state["volatility"])
        state["current_price"] = round(new_price, 2)
        state["high_price"] = round(max(state["high_price"], new_price), 2)
        state["low_price"] = round(min(state["low_price"], new_price), 2)
        state["volume"] += random.randint(1000, 50000)

        prev_close = state["prev_close"]
        change = round(new_price - prev_close, 2)
        change_percent = round((change / prev_close) * 100, 2)

        quote = StockQuote(
            symbol=symbol,
            price=state["current_price"],
            open=round(state["open_price"], 2),
            high=state["high_price"],
            low=state["low_price"],
            volume=state["volume"],
            change=change,
            change_percent=change_percent,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

        await redis_client.set_json(f"stock:quote:{symbol}", quote.model_dump(), ex=60)
        await self._check_alerts(symbol, state["current_price"])
        return quote

    async def get_current_quote(self, symbol: str) -> Optional[StockQuote]:
        cached = await redis_client.get_json(f"stock:quote:{symbol}")
        if cached:
            return StockQuote(**cached)
        return await self.generate_quote(symbol)

    def _generate_kline_days(self, symbol: str, days: int) -> List[KlineData]:
        state = self._stock_state.get(symbol)
        if not state:
            return []
        base = state["base_price"]
        volatility = state["volatility"]
        klines = []
        current_price = base * random.uniform(0.85, 1.15)
        for i in range(days, 0, -1):
            day = datetime.utcnow() - timedelta(days=i)
            open_p = current_price
            close_p = self._random_walk(open_p, volatility * 10)
            high_p = max(open_p, close_p) * (1 + abs(random.gauss(0, 1)) * volatility * 5)
            low_p = min(open_p, close_p) * (1 - abs(random.gauss(0, 1)) * volatility * 5)
            volume = random.randint(500000, 20000000)
            klines.append(KlineData(
                time=day.strftime("%Y-%m-%d"),
                open=round(open_p, 2),
                high=round(high_p, 2),
                low=round(low_p, 2),
                close=round(close_p, 2),
                volume=volume
            ))
            current_price = close_p
        return klines

    def _generate_kline_weeks(self, symbol: str, weeks: int) -> List[KlineData]:
        state = self._stock_state.get(symbol)
        if not state:
            return []
        base = state["base_price"]
        volatility = state["volatility"]
        klines = []
        current_price = base * random.uniform(0.85, 1.15)
        for i in range(weeks, 0, -1):
            week_start = datetime.utcnow() - timedelta(weeks=i, days=datetime.utcnow().weekday())
            open_p = current_price
            close_p = self._random_walk(open_p, volatility * 30)
            high_p = max(open_p, close_p) * (1 + abs(random.gauss(0, 1)) * volatility * 15)
            low_p = min(open_p, close_p) * (1 - abs(random.gauss(0, 1)) * volatility * 15)
            volume = random.randint(5000000, 100000000)
            klines.append(KlineData(
                time=week_start.strftime("%Y-%m-%d"),
                open=round(open_p, 2),
                high=round(high_p, 2),
                low=round(low_p, 2),
                close=round(close_p, 2),
                volume=volume
            ))
            current_price = close_p
        return klines

    def _generate_kline_months(self, symbol: str, months: int) -> List[KlineData]:
        state = self._stock_state.get(symbol)
        if not state:
            return []
        base = state["base_price"]
        volatility = state["volatility"]
        klines = []
        current_price = base * random.uniform(0.7, 1.3)
        today = datetime.utcnow()
        for i in range(months, 0, -1):
            month = today.replace(day=1) - timedelta(days=(today.day - 1) + (i - 1) * 30)
            month = month.replace(day=1)
            open_p = current_price
            close_p = self._random_walk(open_p, volatility * 60)
            high_p = max(open_p, close_p) * (1 + abs(random.gauss(0, 1)) * volatility * 30)
            low_p = min(open_p, close_p) * (1 - abs(random.gauss(0, 1)) * volatility * 30)
            volume = random.randint(20000000, 500000000)
            klines.append(KlineData(
                time=month.strftime("%Y-%m"),
                open=round(open_p, 2),
                high=round(high_p, 2),
                low=round(low_p, 2),
                close=round(close_p, 2),
                volume=volume
            ))
            current_price = close_p
        return klines

    def _generate_kline_minutes(self, symbol: str, minutes: int) -> List[KlineData]:
        state = self._stock_state.get(symbol)
        if not state:
            return []
        base = state["current_price"]
        volatility = state["volatility"]
        klines = []
        current_price = base * random.uniform(0.99, 1.01)
        now = datetime.utcnow().replace(second=0, microsecond=0)
        for i in range(minutes, 0, -1):
            minute = now - timedelta(minutes=i)
            open_p = current_price
            close_p = self._random_walk(open_p, volatility * 2)
            high_p = max(open_p, close_p) * (1 + abs(random.gauss(0, 1)) * volatility)
            low_p = min(open_p, close_p) * (1 - abs(random.gauss(0, 1)) * volatility)
            volume = random.randint(10000, 500000)
            klines.append(KlineData(
                time=minute.strftime("%Y-%m-%d %H:%M"),
                open=round(open_p, 2),
                high=round(high_p, 2),
                low=round(low_p, 2),
                close=round(close_p, 2),
                volume=volume
            ))
            current_price = close_p
        return klines

    def generate_kline_history(
        self, symbol: str, interval: KlineInterval, limit: int = 200
    ) -> List[KlineData]:
        match interval:
            case KlineInterval.MINUTE:
                return self._generate_kline_minutes(symbol, min(limit, 240))
            case KlineInterval.DAY:
                return self._generate_kline_days(symbol, min(limit, 365))
            case KlineInterval.WEEK:
                return self._generate_kline_weeks(symbol, min(limit, 104))
            case KlineInterval.MONTH:
                return self._generate_kline_months(symbol, min(limit, 60))
            case _:
                return []

    def generate_order_book(self, symbol: str) -> OrderBook:
        state = self._stock_state.get(symbol)
        if not state:
            raise ValueError(f"Unknown stock symbol: {symbol}")

        current = state["current_price"]
        tick_size = max(0.01, round(current * 0.0001, 2))

        bids = []
        for i in range(1, 6):
            price = round(current - tick_size * i, 2)
            quantity = random.randint(100, 10000)
            bids.append(OrderBookLevel(price=price, quantity=quantity))

        asks = []
        for i in range(1, 6):
            price = round(current + tick_size * i, 2)
            quantity = random.randint(100, 10000)
            asks.append(OrderBookLevel(price=price, quantity=quantity))

        return OrderBook(
            symbol=symbol,
            bids=bids,
            asks=asks,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def create_alert(
        self, symbol: str, condition: str, target_price: float,
        user_id: str, note: Optional[str] = None
    ) -> Alert:
        import uuid
        alert_id = f"alert_{uuid.uuid4().hex[:12]}"
        alert = Alert(
            id=alert_id,
            symbol=symbol,
            condition=condition,
            target_price=target_price,
            user_id=user_id,
            note=note,
            created_at=datetime.utcnow().isoformat() + "Z",
            triggered=False
        )
        self._alerts[alert_id] = alert
        await redis_client.hset_json("stock:alerts", alert_id, alert.model_dump())
        return alert

    def get_alerts(self, user_id: Optional[str] = None) -> List[Alert]:
        alerts = list(self._alerts.values())
        if user_id:
            alerts = [a for a in alerts if a.user_id == user_id]
        return alerts

    async def delete_alert(self, alert_id: str) -> bool:
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            await redis_client.hdel("stock:alerts", alert_id)
            return True
        return False

    async def _check_alerts(self, symbol: str, current_price: float) -> None:
        notifications = []
        for alert_id, alert in list(self._alerts.items()):
            if alert.symbol != symbol or alert.triggered:
                continue
            triggered = False
            match alert.condition:
                case "gt" if current_price >= alert.target_price:
                    triggered = True
                case "lt" if current_price <= alert.target_price:
                    triggered = True
                case _:
                    pass
            if triggered:
                alert.triggered = True
                await redis_client.hset_json("stock:alerts", alert_id, alert.model_dump())
                notification = AlertNotification(
                    alert_id=alert.id,
                    symbol=alert.symbol,
                    condition=alert.condition,
                    target_price=alert.target_price,
                    current_price=current_price,
                    note=alert.note,
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )
                notifications.append(notification)
                logger.info(f"Alert triggered: {alert_id} for {symbol} at {current_price}")

        cb_errors: List[Exception] = []
        for notification in notifications:
            for callback in self._alert_callbacks:
                try:
                    await callback(notification)
                except Exception as e:
                    cb_errors.append(RuntimeError(f"callback {callback.__name__}: {e}"))
        if cb_errors:
            try:
                raise ExceptionGroup("alert callback errors", cb_errors)
            except ExceptionGroup as eg:
                logger.error("_check_alerts had %d callback errors", len(eg.exceptions))

    def register_alert_callback(self, callback) -> None:
        self._alert_callbacks.append(callback)


stock_service = StockDataService()
