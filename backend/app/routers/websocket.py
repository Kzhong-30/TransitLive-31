from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json
import logging

from app.services.connection_manager import manager
from app.core.models import SubscribeMessage, UnsubscribeMessage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = Query(None, description="用户ID，用于预警推送匹配")
):
    """
    WebSocket 实时行情推送接口

    建立连接后，可发送以下消息：

    **订阅行情**:
    ```json
    {"type": "subscribe", "symbols": ["AAPL", "GOOGL"]}
    ```

    **取消订阅**:
    ```json
    {"type": "unsubscribe", "symbols": ["AAPL"]}
    ```

    **服务端推送行情**:
    ```json
    {"type": "quote", "data": {"symbol": "AAPL", "price": 180.5, ...}}
    ```

    **预警通知推送**:
    ```json
    {"type": "alert", "alert_id": "...", "symbol": "AAPL", ...}
    ```
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
                msg_type = data.get("type")
                if msg_type == "subscribe":
                    symbols = data.get("symbols", [])
                    if isinstance(symbols, list):
                        subscribed = manager.subscribe(websocket, symbols)
                        await websocket.send_json({
                            "type": "subscribed",
                            "symbols": subscribed,
                            "message": f"已订阅 {len(subscribed)} 支股票"
                        })
                elif msg_type == "unsubscribe":
                    symbols = data.get("symbols", [])
                    if isinstance(symbols, list):
                        manager.unsubscribe(websocket, symbols)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "symbols": symbols,
                            "message": "已取消订阅"
                        })
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"未知消息类型: {msg_type}"
                    })
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的JSON格式"
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected, user_id={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
