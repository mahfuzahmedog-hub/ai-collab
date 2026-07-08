import json
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self):
        self._client: Optional[aioredis.Redis] = None

    async def connect(self):
        self._client = await aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        logger.info("Connected to Redis at %s", settings.redis_url)

    async def disconnect(self):
        if self._client:
            await self._client.close()

    async def get(self, key: str) -> Optional[str]:
        return await self._client.get(key) if self._client else None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        if self._client:
            await self._client.set(key, json.dumps(value) if not isinstance(value, str) else value, ex=ttl)

    async def delete(self, key: str):
        if self._client:
            await self._client.delete(key)

    async def publish(self, channel: str, message: dict):
        if self._client:
            await self._client.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str):
        if self._client:
            pubsub = self._client.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        return None

    async def get_channel_messages(self, channel: str, count: int = 50):
        if self._client:
            return await self._client.lrange(channel, -count, -1)
        return []


redis_client = RedisClient()
