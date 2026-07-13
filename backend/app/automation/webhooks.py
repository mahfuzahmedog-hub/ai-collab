from __future__ import annotations
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self):
        self._webhooks: dict[str, dict] = {}

    def register(self, path: str, callback: Callable[[dict], Any], session_scoped: bool = True) -> str:
        webhook_id = f"wh-{uuid.uuid4().hex[:12]}"
        self._webhooks[webhook_id] = {"path": path, "callback": callback, "session_scoped": session_scoped}
        return webhook_id

    def unregister(self, webhook_id: str) -> bool:
        return self._webhooks.pop(webhook_id, None) is not None

    async def handle(self, webhook_id: str, payload: dict) -> Any:
        hook = self._webhooks.get(webhook_id)
        if not hook:
            return {"error": "Webhook not found"}
        try:
            return await hook["callback"](payload)
        except Exception as e:
            logger.error("Webhook %s failed: %s", webhook_id, e)
            return {"error": str(e)}

    def list_webhooks(self) -> list[dict]:
        return [{"id": wid, "path": h["path"], "session_scoped": h["session_scoped"]} for wid, h in self._webhooks.items()]


webhook_handler = WebhookHandler()
