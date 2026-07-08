import asyncio
import json
import logging
from typing import Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, Set[WebSocket]] = {}
        self._user_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, project_id: str, user_id: str = "anonymous"):
        await websocket.accept()
        if project_id not in self._connections:
            self._connections[project_id] = set()
        self._connections[project_id].add(websocket)
        self._user_connections[user_id] = websocket
        logger.info("WebSocket connected: project=%s user=%s", project_id, user_id)

    async def disconnect(self, websocket: WebSocket, project_id: str):
        if project_id in self._connections:
            self._connections[project_id].discard(websocket)
        for uid, ws in list(self._user_connections.items()):
            if ws == websocket:
                del self._user_connections[uid]

    async def broadcast(self, project_id: str, message: dict):
        if project_id not in self._connections:
            return
        data = json.dumps(message)
        dead = set()
        for ws in self._connections[project_id]:
            try:
                await ws.send_text(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections[project_id].discard(ws)

    async def send_to_user(self, user_id: str, message: dict):
        ws = self._user_connections.get(user_id)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                pass

    async def broadcast_event(self, project_id: str, event_type: str, data: dict):
        await self.broadcast(project_id, {"type": event_type, **data})

    def get_active_count(self, project_id: str) -> int:
        return len(self._connections.get(project_id, set()))


ws_manager = ConnectionManager()
