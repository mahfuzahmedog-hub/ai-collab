from fastapi import APIRouter, HTTPException
from app.services.agent_manager import agent_manager

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/")
async def list_agents(project_id: str = None):
    return {"agents": agent_manager.list_agents(project_id)}


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    agent = await agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent.agent.model_dump()


@router.delete("/{agent_id}")
async def remove_agent(agent_id: str):
    await agent_manager.remove_agent(agent_id)
    return {"status": "removed"}
