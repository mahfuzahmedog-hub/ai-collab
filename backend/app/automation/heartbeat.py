from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class HeartbeatManager:
    def __init__(self, interval_seconds: int = 60):
        self.interval = interval_seconds
        self._callbacks: dict[str, Callable] = {}
        self._running = False

    def register(self, name: str, callback: Callable[[], Any]):
        self._callbacks[name] = callback

    def unregister(self, name: str):
        self._callbacks.pop(name, None)

    async def start(self):
        self._running = True
        while self._running:
            await asyncio.sleep(self.interval)
            for name, cb in list(self._callbacks.items()):
                try:
                    await cb() if asyncio.iscoroutinefunction(cb) else cb()
                except Exception as e:
                    logger.error("Heartbeat %s failed: %s", name, e)

    async def stop(self):
        self._running = False


heartbeat_manager = HeartbeatManager()
