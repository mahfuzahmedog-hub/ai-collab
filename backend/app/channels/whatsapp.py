from __future__ import annotations
import logging
from typing import Optional

from app.channels.base import ChannelAdapter, ChannelMessage

logger = logging.getLogger(__name__)


class WhatsAppAdapter(ChannelAdapter):
    def __init__(self, account_sid: str = "", auth_token: str = "", from_number: str = ""):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self._client = None

    async def _ensure_client(self):
        if self._client:
            return
        try:
            from twilio.rest import Client
            self._client = Client(self.account_sid, self.auth_token)
        except ImportError:
            logger.warning("twilio not installed")

    async def send(self, message: ChannelMessage) -> bool:
        await self._ensure_client()
        if not self._client:
            return False
        try:
            self._client.messages.create(
                body=message.text,
                from_=f"whatsapp:{self.from_number}",
                to=f"whatsapp:{message.channel}",
            )
            return True
        except Exception as e:
            logger.error("WhatsApp send failed: %s", e)
            return False

    async def receive(self, payload: dict) -> Optional[ChannelMessage]:
        try:
            return ChannelMessage(
                channel=payload.get("From", "").replace("whatsapp:", ""),
                text=payload.get("Body", ""),
                sender_id=payload.get("From", ""),
                sender_name=payload.get("ProfileName", "Unknown"),
            )
        except Exception as e:
            logger.warning("WhatsApp receive parse failed: %s", e)
            return None

    async def register_webhook(self, url: str) -> bool:
        return True

    def name(self) -> str:
        return "whatsapp"
