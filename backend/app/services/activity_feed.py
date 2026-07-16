from __future__ import annotations
import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Any
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)

_MAX_EVENTS_PER_PROJECT = 500


class ActivityFeed:
    def __init__(self):
        self._events: dict[str, deque[dict]] = defaultdict(lambda: deque(maxlen=_MAX_EVENTS_PER_PROJECT))
        self._subscribed = False

    def _ensure_subscribed(self):
        if self._subscribed:
            return
        self._subscribed = True

        async def _on_event(data: dict):
            etype = data.get("type", "unknown")
            project_id = data.get("project_id") or data.get("id", "").split("-")[0]
            if not project_id:
                return
            entry = {
                "type": etype,
                "summary": _summarize(etype, data),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "data": data,
            }
            self._events[project_id].append(entry)
            await event_bus.publish("activity", {
                "project_id": project_id,
                "entry": entry,
            })

        event_bus.subscribe("*", _on_event)

    def recent(self, project_id: str, limit: int = 50) -> list[dict]:
        return list(self._events.get(project_id, deque()))[-limit:]


def _summarize(etype: str, data: dict) -> str:
    summaries = {
        "message": lambda: f"{data.get('sender_name', '?')}: {data.get('content', '')[:120]}",
        "task_created": lambda: f"Task created: {data.get('title', '?')}",
        "task_transitioned": lambda: f"Task '{data.get('title', '?')}': {data.get('from', '?')} → {data.get('to', '?')}",
        "agent_created": lambda: f"Agent created: {data.get('name', '?')} ({data.get('role', '?')})",
        "agent_removed": lambda: f"Agent removed: {data.get('agent_id', '?')}",
        "agent_updated": lambda: f"Agent updated: {data.get('name', '?')}",
        "channel_created": lambda: f"Channel created: {data.get('name', '?')}",
        "channel_deleted": lambda: f"Channel deleted",
        "project_updated": lambda: f"Project updated",
        "approval_created": lambda: f"Approval needed: {data.get('action', '?')}",
        "approval_updated": lambda: f"Approval: {data.get('status', '?')}",
        "execution_log": lambda: f"Tool: {data.get('tool', '?')} by {data.get('agent_name', '?')}",
        "notification": lambda: f"Notification: {data.get('title', '?')}",
    }
    handler = summaries.get(etype)
    return handler() if handler else f"Event: {etype}"


activity_feed = ActivityFeed()
activity_feed._ensure_subscribed()
