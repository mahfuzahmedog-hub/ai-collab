from fastapi import APIRouter, HTTPException
from app.models.task import Task, TaskStatus

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_tasks_store: dict[str, Task] = {}


@router.post("/")
async def create_task(task: Task):
    task.id = f"task-{__import__('uuid').uuid4().hex[:8]}"
    _tasks_store[task.id] = task
    return task.model_dump()


@router.get("/")
async def list_tasks(project_id: str = None):
    tasks = _tasks_store.values()
    if project_id:
        tasks = [t for t in tasks if t.project_id == project_id]
    return {"tasks": [t.model_dump() for t in tasks]}


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = _tasks_store.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.model_dump()


@router.patch("/{task_id}/status")
async def update_task_status(task_id: str, status_data: dict):
    task = _tasks_store.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.status = TaskStatus(status_data.get("status", task.status.value))
    return task.model_dump()
