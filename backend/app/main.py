from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.redis_client import redis_client
from app.routers import stocks, alerts, websocket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 实时股票行情数据服务 API

基于 FastAPI + WebSocket + Redis 构建的金融实时行情服务。

### 主要功能
- **HTTP API**: 股票列表、历史K线、盘口深度、价格预警管理
- **WebSocket**: 实时行情推送（1秒间隔），支持多股票订阅
- **价格预警**: 创建条件预警，触发时通过 WebSocket 推送通知

### 使用指南
1. 通过 `GET /stocks` 查看支持的股票列表
2. 通过 WebSocket 连接 `/ws` 建立连接
3. 发送订阅消息 `{"type":"subscribe","symbols":["AAPL","600519"]}`
4. 创建预警通过 `POST /alerts`
    """,
    contact={
        "name": "Stock Market Data Service",
    },
    license_info={
        "name": "MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(websocket.router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await redis_client.connect()
    from app.services.stock_service import stock_service
    await stock_service._load_from_redis()
    logger.info(f"Loaded {len(stock_service.get_all_stocks())} stock symbols")
    logger.info(f"Loaded {len(stock_service.get_alerts())} active alerts")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
    await redis_client.close()


@app.get("/", tags=["system"], summary="健康检查")
async def root():
    """服务健康检查端点"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health", tags=["system"], summary="健康状态")
async def health():
    """详细健康状态检查"""
    from app.services.connection_manager import manager
    redis_available = redis_client.get_client() is not None
    return {
        "status": "healthy" if redis_available else "degraded",
        "components": {
            "redis": "connected" if redis_available else "disconnected (fallback mode)",
            "websocket_connections": manager.active_connections_count(),
            "broadcast_running": manager.is_broadcast_running,
            "broadcast_task_id": id(manager._broadcast_task) if manager._broadcast_task else None
        }
    }
