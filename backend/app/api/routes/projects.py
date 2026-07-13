from fastapi import APIRouter, HTTPException
from app.models.project import Project, ProjectStatus
from app.services.agent_manager import agent_manager
from app.core.event_bus import event_bus

router = APIRouter(prefix="/api/projects", tags=["projects"])

_projects_store: dict[str, Project] = {}


@router.post("/")
async def create_project(project: Project):
    project.id = f"proj-{__import__('uuid').uuid4().hex[:8]}"
    _projects_store[project.id] = project
    boss = await agent_manager.create_coworker(project.id)
    await boss.initialize_workspace(project)
    return {"project_id": project.id, "boss_name": boss.name}


@router.get("/")
async def list_projects():
    return {"projects": [p.model_dump() for p in _projects_store.values()]}


@router.get("/{project_id}")
async def get_project(project_id: str):
    project = _projects_store.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project.model_dump()


@router.post("/{project_id}/agents")
async def add_agent(project_id: str, agent_data: dict):
    from app.models.agent import AgentRole
    project = _projects_store.get(project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    role = AgentRole(agent_data.get("role", "backend_engineer"))
    worker = await agent_manager.create_worker(
        project_id,
        agent_data.get("name", "Worker"),
        role,
    )
    project.agent_ids.append(worker.id)
    return worker.agent.model_dump()
