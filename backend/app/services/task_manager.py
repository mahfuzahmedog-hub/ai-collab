from __future__ import annotations
import asyncio
import logging
from typing import Optional
from app.models.task import Task, TaskStatus, TaskPriority
from app.core.event_bus import event_bus
from app.db.repository import save_task, update_task_fields

logger = logging.getLogger(__name__)

_VALID_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.waiting: {TaskStatus.planning, TaskStatus.assigned, TaskStatus.cancelled},
    TaskStatus.planning: {TaskStatus.working, TaskStatus.blocked, TaskStatus.cancelled},
    TaskStatus.assigned: {TaskStatus.working, TaskStatus.blocked, TaskStatus.cancelled},
    TaskStatus.working: {TaskStatus.review, TaskStatus.blocked, TaskStatus.cancelled},
    TaskStatus.blocked: {TaskStatus.waiting, TaskStatus.working, TaskStatus.cancelled},
    TaskStatus.review: {TaskStatus.completed, TaskStatus.revision, TaskStatus.cancelled},
    TaskStatus.testing: {TaskStatus.completed, TaskStatus.revision, TaskStatus.cancelled},
    TaskStatus.revision: {TaskStatus.working, TaskStatus.review, TaskStatus.cancelled},
    TaskStatus.completed: set(),
    TaskStatus.rejected: set(),
    TaskStatus.cancelled: set(),
}


async def transition_task(task: Task, new_status: TaskStatus) -> Task:
    old_status = task.status
    allowed = _VALID_TRANSITIONS.get(old_status, set())
    if new_status not in allowed:
        logger.warning("Invalid transition %s -> %s for task %s", old_status, new_status, task.id)
        return task
    task.status = new_status
    await update_task_fields(task.project_id, task.id, status=new_status.value)
    await event_bus.publish("task_transitioned", {
        "task_id": task.id, "project_id": task.project_id,
        "from": old_status.value, "to": new_status.value,
        "title": task.title,
    })
    return task


async def create_task(
    project_id: str,
    title: str,
    description: str = "",
    priority: TaskPriority = TaskPriority.medium,
    assigned_to: Optional[str] = None,
    assigned_by: Optional[str] = None,
) -> Task:
    task = Task(
        project_id=project_id, title=title, description=description,
        priority=priority, assigned_to=assigned_to, assigned_by=assigned_by,
    )
    if assigned_to:
        task.status = TaskStatus.assigned
    await save_task(task)
    await event_bus.publish("task_created", task.model_dump())
    return task


async def cancel_task(task: Task) -> Task:
    return await transition_task(task, TaskStatus.cancelled)


async def retry_task(task: Task) -> Task:
    return await transition_task(task, TaskStatus.working)
