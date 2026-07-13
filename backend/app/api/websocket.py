from __future__ import annotations
import logging
from typing import Any

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/ws/{project_id}")
async def project_ws(websocket: WebSocket, project_id: str):
    await websocket.accept()
    logger.info("WebSocket connected for project %s", project_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue
            msg_type = msg.get("type", "")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "ts": msg.get("ts")})
            elif msg_type == "message":
                from app.services.agent_manager import agent_manager
                if agent_manager.boss:
                    await agent_manager.boss.handle_user_request(
                        project_id, msg.get("content", ""), msg.get("channel", "general")
                    )
                await websocket.send_json({"type": "ack", "status": "processing"})
            else:
                await websocket.send_json({"type": "unknown", "msg_type": msg_type})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for project %s", project_id)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
