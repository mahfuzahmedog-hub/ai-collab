from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ChannelMessage:
    channel: str
    text: str
    sender_id: str
    sender_name: str
    thread_id: Optional[str] = None
    attachments: list[dict] = None
    metadata: dict[str, Any] = None


class ChannelAdapter(ABC):
    @abstractmethod
    async def send(self, message: ChannelMessage) -> bool:
        pass

    @abstractmethod
    async def receive(self, payload: dict) -> Optional[ChannelMessage]:
        pass

    @abstractmethod
    async def register_webhook(self, url: str) -> bool:
        pass

    @abstractmethod
    def name(self) -> str:
        pass
