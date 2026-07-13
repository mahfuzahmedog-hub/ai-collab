from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional

from app.graph.types import Interrupt

logger = logging.getLogger(__name__)


class InterruptContext:
    def __init__(self):
        self._pending: dict[str, list[dict]] = {}
        self._resume_events: dict[str, asyncio.Event] = {}

    def has_pending(self, thread_id: str) -> bool:
        return thread_id in self._pending and bool(self._pending[thread_id])

    def get_pending(self, thread_id: str) -> list[dict]:
        return self._pending.get(thread_id, [])

    async def resolve(self, thread_id: str, resume: bool = True, data: Optional[dict] = None):
        self._pending.pop(thread_id, None)
        event = self._resume_events.pop(thread_id, None)
        if event:
            event.set()

    def suspend(self, thread_id: str, value: Any) -> Interrupt:
        self._pending.setdefault(thread_id, []).append({"value": value})
        return Interrupt(value)


interrupt_context = InterruptContext()


async def interrupt(value: Any) -> Any:
    raise Interrupt(value)
