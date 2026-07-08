import asyncio
import logging
from datetime import datetime
from app.models.task import Task, TaskStatus
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self._running = False
        self._tasks: dict[str, Task] = {}

    def register_task(self, task: Task):
        self._tasks[task.id] = task

    def update_status(self, task_id: str, status: TaskStatus):
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            if status == TaskStatus.completed:
                task.completed_at = datetime.utcnow()

    def get_next_available(self) -> list[Task]:
        available = []
        for task in self._tasks.values():
            if task.status == TaskStatus.assigned and not task.parent_task_id:
                deps_met = all(
                    dep_id in self._tasks and self._tasks[dep_id].status == TaskStatus.completed
                    for dep_id in task.depends_on
                )
                if deps_met:
                    available.append(task)
        return available

    def get_tasks_by_agent(self, agent_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.assigned_to == agent_id]

    def get_blocked_tasks(self) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.blocked]

    async def start(self):
        self._running = True
        while self._running:
            await asyncio.sleep(5)

    async def stop(self):
        self._running = False


task_scheduler = TaskScheduler()
