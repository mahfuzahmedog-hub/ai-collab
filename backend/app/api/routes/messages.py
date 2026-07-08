from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.handlers import handle_websocket

router = APIRouter()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await handle_websocket(websocket, project_id)


@router.websocket("/ws/{project_id}/{user_id}")
async def websocket_endpoint_with_user(websocket: WebSocket, project_id: str, user_id: str):
    await handle_websocket(websocket, project_id, user_id)
