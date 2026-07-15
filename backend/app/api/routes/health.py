from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check():
    from app.websocket.manager import ws_manager
    total = sum(len(ws) for ws in ws_manager._connections.values()) if ws_manager._connections else 0
    return {
        "status": "healthy",
        "app": "AI Collaboration Platform",
        "version": "0.1.0",
        "ws_connections": total,
    }


@router.get("/info")
async def info():
    from app.llm import llm_router
    return {
        "providers": llm_router.list_providers(),
        "default_provider": settings.llm_default_provider,
    }
