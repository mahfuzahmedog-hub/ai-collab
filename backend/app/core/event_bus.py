import asyncio
import json
import logging
from typing import Any, Callable, Coroutine
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], Coroutine]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[dict[str, Any]], Coroutine]):
        self._subscribers[event_type].append(callback)
        logger.debug("Subscribed to %s", event_type)

    def unsubscribe(self, event_type: str, callback: Callable[[dict[str, Any]], Coroutine]):
        if callback in self._subscribers.get(event_type, []):
            self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, data: dict[str, Any]):
        logger.info("Event: %s | %s", event_type, json.dumps(data, default=str)[:200])
        tasks = []
        for cb in self._subscribers.get(event_type, []):
            tasks.append(asyncio.create_task(cb(data)))
        for cb in self._subscribers.get("*", []):
            tasks.append(asyncio.create_task(cb({**data, "type": event_type})))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


event_bus = EventBus()
