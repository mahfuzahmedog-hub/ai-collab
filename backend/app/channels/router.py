from __future__ import annotations
import logging
from typing import Optional

from app.channels.base import ChannelAdapter, ChannelMessage

logger = logging.getLogger(__name__)


class ChannelRouter:
    def __init__(self):
        self._adapters: dict[str, ChannelAdapter] = {}

    def register(self, adapter: ChannelAdapter):
        self._adapters[adapter.name()] = adapter
        logger.info("Registered channel adapter: %s", adapter.name())

    def get(self, name: str) -> Optional[ChannelAdapter]:
        return self._adapters.get(name)

    async def route(self, message: ChannelMessage, channel_type: str) -> bool:
        adapter = self._adapters.get(channel_type)
        if not adapter:
            logger.warning("No adapter for channel type: %s", channel_type)
            return False
        return await adapter.send(message)

    async def route_incoming(self, channel_type: str, payload: dict) -> Optional[ChannelMessage]:
        adapter = self._adapters.get(channel_type)
        if not adapter:
            return None
        return await adapter.receive(payload)

    def list_adapters(self) -> list[str]:
        return list(self._adapters.keys())


channel_router = ChannelRouter()
