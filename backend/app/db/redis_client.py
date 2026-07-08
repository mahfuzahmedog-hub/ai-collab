import json
import logging
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as aioredis
    _redis_available = True
except ImportError:
    aioredis = None
    _redis_available = False
    logger.warning("redis package not installed — running without Redis")


class _FakePubSub:
    async def listen(self):
        return
        yield


class RedisClient:
    def __init__(self):
        self._client: Any = None

    async def connect(self):
        if not _redis_available:
            logger.info("Redis disabled (package not available)")
            return
        try:
            self._client = await aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
            logger.info("Connected to Redis at %s", settings.redis_url)
        except Exception as e:
            logger.warning("Redis connection failed (continuing without it): %s", e)

    async def disconnect(self):
        if self._client and _redis_available:
            try:
                await self._client.close()
            except Exception:
                pass

    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key) if self._client and _redis_available else None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        if self._client and _redis_available:
            await self._client.set(key, json.dumps(value) if not isinstance(value, str) else value, ex=ttl)

    async def delete(self, key: str):
        if self._client and _redis_available:
            await self._client.delete(key)

    async def publish(self, channel: str, message: dict):
        if self._client and _redis_available:
            await self._client.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str):
        if self._client and _redis_available:
            pubsub = self._client.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        return _FakePubSub()

    async def get_channel_messages(self, channel: str, count: int = 50):
        if self._client and _redis_available:
            return await self._client.lrange(channel, -count, -1)
        return []


redis_client = RedisClient()
