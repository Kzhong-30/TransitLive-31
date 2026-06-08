import asyncio
import json
import logging
from typing import Dict, Set, List, Optional
from fastapi import WebSocket

from app.services.stock_service import stock_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: Dict[WebSocket, Set[str]] = {}
        self._user_connections: Dict[str, WebSocket] = {}
        self._broadcast_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        await websocket.accept()
        self._connections[websocket] = set()
        if user_id:
            self._user_connections[user_id] = websocket
        if self._broadcast_task is None or self._broadcast_task.done():
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        stock_service.register_alert_callback(self._send_alert_notification)

    def disconnect(self, websocket: WebSocket):
        if websocket in self._connections:
            del self._connections[websocket]
        for uid, ws in list(self._user_connections.items()):
            if ws == websocket:
                del self._user_connections[uid]
                break

    def subscribe(self, websocket: WebSocket, symbols: List[str]):
        if websocket in self._connections:
            valid_symbols = {s for s in symbols if stock_service.get_stock_info(s)}
            self._connections[websocket].update(valid_symbols)
            return list(valid_symbols)
        return []

    def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        if websocket in self._connections:
            self._connections[websocket].difference_update(symbols)

    def get_subscriptions(self, websocket: WebSocket) -> List[str]:
        if websocket in self._connections:
            return list(self._connections[websocket])
        return []

    async def _broadcast_loop(self):
        logger.info("Starting broadcast loop")
        while True:
            if not self._connections:
                await asyncio.sleep(settings.PUSH_INTERVAL)
                continue
            try:
                all_symbols = set()
                for syms in self._connections.values():
                    all_symbols.update(syms)
                quotes = {}
                for symbol in all_symbols:
                    try:
                        quote = await stock_service.generate_quote(symbol)
                        quotes[symbol] = quote.model_dump()
                    except Exception as e:
                        logger.error(f"Error generating quote for {symbol}: {e}")
                for ws, subs in self._connections.items():
                    for symbol in subs:
                        if symbol in quotes:
                            try:
                                await ws.send_json({
                                    "type": "quote",
                                    "data": quotes[symbol]
                                })
                            except Exception as e:
                                logger.debug(f"Error sending to client: {e}")
            except Exception as e:
                logger.error(f"Broadcast loop error: {e}")
            await asyncio.sleep(settings.PUSH_INTERVAL)

    async def _send_alert_notification(self, notification):
        message = notification.model_dump()
        for ws, subs in self._connections.items():
            if notification.symbol in subs:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.debug(f"Error sending alert to client: {e}")

    def active_connections_count(self) -> int:
        return len(self._connections)


manager = ConnectionManager()
