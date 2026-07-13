from __future__ import annotations
import logging
from typing import Optional

from app.channels.base import ChannelAdapter, ChannelMessage

logger = logging.getLogger(__name__)


class TelegramAdapter(ChannelAdapter):
    def __init__(self, token: str = ""):
        self.token = token
        self._bot = None

    async def _ensure_bot(self):
        if self._bot:
            return
        try:
            from telegram import Bot
            self._bot = Bot(token=self.token)
        except ImportError:
            logger.warning("python-telegram-bot not installed")

    async def send(self, message: ChannelMessage) -> bool:
        await self._ensure_bot()
        if not self._bot:
            return False
        try:
            await self._bot.send_message(chat_id=message.channel, text=message.text)
            return True
        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            return False

    async def receive(self, payload: dict) -> Optional[ChannelMessage]:
        try:
            msg = payload.get("message", {})
            return ChannelMessage(
                channel=str(msg.get("chat", {}).get("id", "")),
                text=msg.get("text", ""),
                sender_id=str(msg.get("from", {}).get("id", "")),
                sender_name=msg.get("from", {}).get("first_name", "Unknown"),
            )
        except Exception as e:
            logger.warning("Telegram receive parse failed: %s", e)
            return None

    async def register_webhook(self, url: str) -> bool:
        await self._ensure_bot()
        if not self._bot:
            return False
        try:
            await self._bot.set_webhook(url=url)
            return True
        except Exception as e:
            logger.error("Telegram webhook failed: %s", e)
            return False

    def name(self) -> str:
        return "telegram"
