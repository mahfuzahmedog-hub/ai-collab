from __future__ import annotations
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["aios"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "aios-backend"}


@router.get("/agents")
async def list_agents(project_id: Optional[str] = Query(None)) -> dict:
    from app.services.agent_manager import agent_manager
    agents = agent_manager.list_agents(project_id)
    return {"agents": agents, "count": len(agents)}


@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str) -> dict:
    from app.services.agent_manager import agent_manager
    agent = await agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.agent.model_dump()


@router.get("/projects/{project_id}/workflows")
async def list_workflows(project_id: str) -> dict:
    return {"workflows": [], "count": 0}


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, payload: dict) -> dict:
    return {"workflow_id": workflow_id, "status": "accepted", "context": {}}


@router.get("/memory/{project_id}")
async def list_memory(project_id: str, limit: int = 50) -> dict:
    from app.memory.manager import memory_manager
    memories = await memory_manager.list_by_project(project_id, limit=limit)
    return {"memories": memories, "count": len(memories)}


@router.get("/skills")
async def list_skills() -> dict:
    from app.memory.manager import memory_manager
    skills = await memory_manager.list_skills(limit=100)
    return {"skills": skills, "count": len(skills)}


@router.get("/sessions")
async def list_sessions(project_id: Optional[str] = Query(None)) -> dict:
    # ponytail: sessions module removed — return empty
    return {"sessions": [], "count": 0, "note": "sessions module removed"}


@router.get("/observability/metrics")
async def observability_metrics() -> dict:
    from app.observability.metrics import metrics_collector
    return metrics_collector.global_summary()


@router.get("/integrations")
async def list_integrations() -> dict:
    from app.integrations import integration_registry
    return {"integrations": integration_registry.list()}


@router.get("/mcp/servers")
async def list_mcp_servers() -> dict:
    # ponytail: mcp module removed — return empty
    return {"servers": [], "note": "mcp module removed"}


@router.get("/plugins")
async def list_plugins() -> dict:
    from app.plugins.loader import plugin_loader
    return {"plugins": list(plugin_loader._plugins.keys())}
