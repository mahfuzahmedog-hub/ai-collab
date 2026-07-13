from __future__ import annotations
import json
import logging
from typing import Optional

from app.channels.base import ChannelAdapter, ChannelMessage

logger = logging.getLogger(__name__)


class SlackAdapter(ChannelAdapter):
    def __init__(self, token: str = "", signing_secret: str = ""):
        self.token = token
        self.signing_secret = signing_secret
        self._client = None

    async def _ensure_client(self):
        if self._client:
            return
        try:
            from slack_sdk import WebClient
            self._client = WebClient(token=self.token)
        except ImportError:
            logger.warning("slack-sdk not installed")

    async def send(self, message: ChannelMessage) -> bool:
        await self._ensure_client()
        if not self._client:
            return False
        try:
            self._client.chat_postMessage(channel=message.channel, text=message.text)
            return True
        except Exception as e:
            logger.error("Slack send failed: %s", e)
            return False

    async def receive(self, payload: dict) -> Optional[ChannelMessage]:
        try:
            event = payload.get("event", payload)
            if event.get("type") == "message" and "subtype" not in event:
                return ChannelMessage(
                    channel=event.get("channel", ""),
                    text=event.get("text", ""),
                    sender_id=event.get("user", ""),
                    sender_name=event.get("user", "Unknown"),
                )
            return None
        except Exception as e:
            logger.warning("Slack receive parse failed: %s", e)
            return None

    async def register_webhook(self, url: str) -> bool:
        return True

    def name(self) -> str:
        return "slack"
