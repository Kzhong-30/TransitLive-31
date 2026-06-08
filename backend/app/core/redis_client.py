import redis.asyncio as redis
from typing import Optional
import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def connect(cls):
        if cls._client is None or cls._client.connection_pool is None:
            kwargs = {
                "host": settings.REDIS_HOST,
                "port": settings.REDIS_PORT,
                "db": settings.REDIS_DB,
                "decode_responses": True,
            }
            if settings.REDIS_PASSWORD:
                kwargs["password"] = settings.REDIS_PASSWORD
            cls._client = redis.Redis(**kwargs)
            try:
                await cls._client.ping()
                logger.info("Connected to Redis successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed, will use in-memory fallback: {e}")
                cls._client = None

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.close()
            cls._client = None

    @classmethod
    async def set_json(cls, key: str, value: dict, ex: int = None):
        if cls._client:
            await cls._client.set(key, json.dumps(value), ex=ex)

    @classmethod
    async def get_json(cls, key: str) -> Optional[dict]:
        if cls._client:
            data = await cls._client.get(key)
            if data:
                return json.loads(data)
        return None

    @classmethod
    async def hset_json(cls, name: str, key: str, value: dict):
        if cls._client:
            await cls._client.hset(name, key, json.dumps(value))

    @classmethod
    async def hget_json(cls, name: str, key: str) -> Optional[dict]:
        if cls._client:
            data = await cls._client.hget(name, key)
            if data:
                return json.loads(data)
        return None

    @classmethod
    async def hgetall_json(cls, name: str) -> dict:
        result = {}
        if cls._client:
            data = await cls._client.hgetall(name)
            for k, v in data.items():
                result[k] = json.loads(v)
        return result

    @classmethod
    async def hdel(cls, name: str, *keys: str):
        if cls._client:
            await cls._client.hdel(name, *keys)

    @classmethod
    async def rpush_json(cls, name: str, value: dict):
        if cls._client:
            await cls._client.rpush(name, json.dumps(value))

    @classmethod
    async def lrange_json(cls, name: str, start: int, end: int) -> list:
        result = []
        if cls._client:
            data = await cls._client.lrange(name, start, end)
            for item in data:
                result.append(json.loads(item))
        return result


redis_client = RedisClient()
