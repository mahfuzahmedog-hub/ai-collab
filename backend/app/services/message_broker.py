import json
import logging
from typing import Callable
from app.db.redis_client import redis_client
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)


class MessageBroker:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    async def publish(self, channel: str, message: dict):
        await redis_client.publish(channel, message)
        await event_bus.publish(f"broker:{channel}", message)

    async def subscribe(self, channel: str, handler: Callable):
        if channel not in self._handlers:
            self._handlers[channel] = []
            pubsub = await redis_client.subscribe(channel)
            if pubsub:
                asyncio.create_task(self._listen(pubsub, channel))
        self._handlers[channel].append(handler)

    async def _listen(self, pubsub, channel: str):
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                for handler in self._handlers.get(channel, []):
                    try:
                        await handler(data)
                    except Exception as e:
                        logger.error("Handler error on channel %s: %s", channel, e)

    def get_project_channel(self, project_id: str) -> str:
        return f"project:{project_id}"

    def get_agent_channel(self, agent_id: str) -> str:
        return f"agent:{agent_id}"


import asyncio
message_broker = MessageBroker()
