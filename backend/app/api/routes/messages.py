from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from typing import Optional
from app.websocket.handlers import handle_websocket
from app.websocket.manager import ws_manager
from app.models.message import Message
from app.db.repository import save_message, load_project_messages, delete_message

router = APIRouter()


# ─── WebSocket endpoints (existing) ───

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await handle_websocket(websocket, project_id)


@router.websocket("/ws/{project_id}/{user_id}")
async def websocket_endpoint_with_user(websocket: WebSocket, project_id: str, user_id: str):
    await handle_websocket(websocket, project_id, user_id)


# ─── REST API endpoints (new) ───

@router.post("/api/messages")
async def send_message(msg: Message):
    """Send a message. Saved to DB and broadcast via WebSocket."""
    await save_message(msg)
    await ws_manager.broadcast(msg.project_id, {
        "type": "new_message",
        "message": msg.model_dump(),
    })
    return {"success": True, "message": msg.model_dump()}


@router.get("/api/messages")
async def list_messages(
    project_id: str = Query(..., description="Project ID"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    limit: int = Query(100, description="Max messages"),
):
    """List messages for a project, optionally filtered by channel."""
    msgs = await load_project_messages(project_id, limit=limit)
    if channel:
        msgs = [m for m in msgs if m.channel == channel]
    return {"messages": [m.model_dump() for m in msgs], "count": len(msgs)}


@router.get("/api/messages/{message_id}")
async def get_message(message_id: str, project_id: str = Query(...)):
    """Get a single message by ID."""
    msgs = await load_project_messages(project_id, limit=1000)
    for m in msgs:
        if m.id == message_id:
            return {"message": m.model_dump()}
    raise HTTPException(status_code=404, detail="Message not found")


@router.delete("/api/messages/{message_id}")
async def remove_message(message_id: str, project_id: str = Query(...)):
    """Delete a message."""
    ok = await delete_message(project_id, message_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Message not found")
    await ws_manager.broadcast(project_id, {
        "type": "message_deleted",
        "message_id": message_id,
    })
    return {"success": True}
