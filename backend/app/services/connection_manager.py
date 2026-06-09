import asyncio
import json
import logging
from typing import Dict, Set, List, Optional
from typing import Self
from fastapi import WebSocket

from app.services.stock_service import stock_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    _instance: Optional[Self] = None

    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connections: Dict[WebSocket, Set[str]] = {}
            cls._instance._user_connections: Dict[str, WebSocket] = {}
            cls._instance._broadcast_task: Optional[asyncio.Task] = None
        return cls._instance

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> None:
        await websocket.accept()
        self._connections[websocket] = set()
        if user_id:
            self._user_connections[user_id] = websocket
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())
            logger.info("Broadcast loop started (task_id=%s)", id(self._broadcast_task))
        stock_service.register_alert_callback(self._send_alert_notification)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            del self._connections[websocket]
        for uid, ws in list(self._user_connections.items()):
            if ws == websocket:
                del self._user_connections[uid]
                break
        if not self._connections and self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
            logger.info("No active connections, broadcast loop cancelled")
            self._broadcast_task = None

    def subscribe(self, websocket: WebSocket, symbols: List[str]) -> List[str]:
        if websocket in self._connections:
            valid_symbols = {s for s in symbols if stock_service.get_stock_info(s)}
            self._connections[websocket].update(valid_symbols)
            return list(valid_symbols)
        return []

    def unsubscribe(self, websocket: WebSocket, symbols: List[str]) -> None:
        if websocket in self._connections:
            self._connections[websocket].difference_update(symbols)

    def get_subscriptions(self, websocket: WebSocket) -> List[str]:
        if websocket in self._connections:
            return list(self._connections[websocket])
        return []

    async def _broadcast_loop(self) -> None:
        logger.info("Starting broadcast loop")
        try:
            while True:
                all_symbols = set()
                for syms in self._connections.values():
                    all_symbols.update(syms)
                quotes: Dict[str, dict] = {}
                errors: List[Exception] = []
                for symbol in all_symbols:
                    try:
                        quote = await stock_service.generate_quote(symbol)
                        quotes[symbol] = quote.model_dump()
                    except Exception as e:
                        errors.append(RuntimeError(f"quote {symbol}: {e}"))
                send_errors: List[Exception] = []
                for ws, subs in self._connections.items():
                    for symbol in subs:
                        if symbol in quotes:
                            try:
                                await ws.send_json({
                                    "type": "quote",
                                    "data": quotes[symbol]
                                })
                            except Exception as e:
                                send_errors.append(RuntimeError(f"send {symbol}->ws: {e}"))
                all_errors = errors + send_errors
                if all_errors:
                    try:
                        raise ExceptionGroup("broadcast batch errors", all_errors)
                    except ExceptionGroup as eg:
                        logger.warning("Broadcast encountered %d sub-errors", len(eg.exceptions))
                await asyncio.sleep(settings.PUSH_INTERVAL)
        except asyncio.CancelledError:
            logger.info("Broadcast loop cancelled cleanly")
            raise

    async def _send_alert_notification(self, notification) -> None:
        message = notification.model_dump()
        send_errors: List[Exception] = []
        for ws, subs in self._connections.items():
            if notification.symbol in subs:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    send_errors.append(RuntimeError(f"alert push: {e}"))
        if send_errors:
            try:
                raise ExceptionGroup("alert push errors", send_errors)
            except ExceptionGroup as eg:
                logger.warning("Alert push encountered %d sub-errors", len(eg.exceptions))

    def active_connections_count(self) -> int:
        return len(self._connections)

    @property
    def is_broadcast_running(self) -> bool:
        return self._broadcast_task is not None and not self._broadcast_task.done()


manager = ConnectionManager()
