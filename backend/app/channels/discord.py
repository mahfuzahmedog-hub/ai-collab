from __future__ import annotations
import logging
from typing import Optional

from app.channels.base import ChannelAdapter, ChannelMessage

logger = logging.getLogger(__name__)


class DiscordAdapter(ChannelAdapter):
    def __init__(self, token: str = ""):
        self.token = token
        self._client = None

    async def _ensure_client(self):
        if self._client:
            return
        try:
            import discord
            self._client = discord.Client(intents=discord.Intents.default())
        except ImportError:
            logger.warning("discord.py not installed")

    async def send(self, message: ChannelMessage) -> bool:
        await self._ensure_client()
        if not self._client:
            return False
        try:
            channel = await self._client.fetch_channel(int(message.channel))
            await channel.send(message.text)
            return True
        except Exception as e:
            logger.error("Discord send failed: %s", e)
            return False

    async def receive(self, payload: dict) -> Optional[ChannelMessage]:
        try:
            d = payload.get("d", payload)
            return ChannelMessage(
                channel=str(d.get("channel_id", "")),
                text=d.get("content", ""),
                sender_id=str(d.get("author", {}).get("id", "")),
                sender_name=d.get("author", {}).get("username", "Unknown"),
            )
        except Exception as e:
            logger.warning("Discord receive parse failed: %s", e)
            return None

    async def register_webhook(self, url: str) -> bool:
        return True

    def name(self) -> str:
        return "discord"
