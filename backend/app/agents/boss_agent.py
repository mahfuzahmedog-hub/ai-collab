import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from app.agents.base_agent import BaseAgent
from app.agents.worker_agent import WorkerAgent
from app.models.agent import Agent, AgentStatus, AgentRole
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project, ProjectStatus
from app.models.message import Message
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)

BOSS_SYSTEM_PROMPT = """You are the Boss Agent, the engineering manager of an AI collaboration team.

Your responsibilities:
1. Receive project requests from the user
2. Analyze complexity and estimate effort
3. Create a team of specialized agents
4. Assign roles and delegate work
5. Track progress and dependencies
6. Coordinate communication between team members
7. Resolve disagreements and unblock work
8. Review deliverables and approve releases
9. Keep the user informed of progress

You communicate like an experienced engineering manager - professional, clear, and decisive.
You always introduce new team members when they join.
You check in on progress regularly.
You make sure nothing falls through the cracks."""


class BossAgent(BaseAgent):
    def __init__(self, agent: Agent):
        super().__init__(agent)
        self.team: dict[str, WorkerAgent] = {}
        self.project: Optional[Project] = None
        self.tasks: dict[str, Task] = {}
        self._event_handlers = []

    def _system_prompt(self) -> str:
        return BOSS_SYSTEM_PROMPT

    async def initialize_project(self, project: Project):
        self.project = project
        self.agent.project_id = project.id
        await self.send_message(project.id, f"🚀 Project '{project.title}' initialized. I am your Boss Agent, {self.name}. Let me analyze this project and build a team.", msg_type="system")

    async def handle_user_request(self, project_id: str, user_message: str):
        prompt = f"""The user has sent this message:
{user_message}

Current project: {self.project.title if self.project else 'No project'}
Team members: {', '.join(f'{a.name} ({a.role.value})' for a in self.team.values()) if self.team else 'No team yet'}

Respond professionally as the Boss Agent. If this is a new project request, analyze it and decide what team you need. If there's an existing team, delegate work appropriately."""

        response = await self.think(prompt)
        await self.send_message(project_id, response)

    async def create_team(self, required_roles: list[dict]):
        if not self.project:
            return

        await self.send_message(self.project.id, f"📋 Building team for '{self.project.title}'...", msg_type="system")

        for role_info in required_roles:
            role = role_info.get("role", AgentRole.backend)
            name = role_info.get("name", f"{role.value.title()}-{len(self.team) + 1}")
            skills = role_info.get("skills", [role.value])

            agent_model = Agent(
                name=name,
                role=role,
                project_id=self.project.id,
                skills=skills,
                personality=role_info.get("personality", "professional and collaborative"),
            )
            worker = WorkerAgent(agent_model)
            self.team[agent_model.id] = worker
            self.project.agent_ids.append(agent_model.id)

            await worker.send_message(self.project.id, f"👋 Hello team! I'm {name}, your {role.value}. Ready to contribute!")
            await asyncio.sleep(0.5)

        await self.send_message(
            self.project.id,
            f"✅ Team created with {len(self.team)} members. Let's start working!",
            msg_type="system",
        )

    async def create_task(self, title: str, description: str = "", priority: TaskPriority = TaskPriority.medium, assigned_role: Optional[str] = None) -> Task:
        task = Task(
            project_id=self.project.id,
            title=title,
            description=description,
            priority=priority,
            assigned_by=self.id,
        )
        self.tasks[task.id] = task
        self.project.task_ids.append(task.id)

        if assigned_role:
            for agent_id, worker in self.team.items():
                if worker.agent.role.value == assigned_role or assigned_role in worker.agent.skills:
                    task.assigned_to = agent_id
                    task.status = TaskStatus.assigned
                    worker.assign_task(task)
                    await self.send_message(
                        self.project.id,
                        f"📌 {worker.name}: I'm assigning you '{task.title}'.\n{description}",
                        mentions=[worker.name],
                    )
                    break

        await event_bus.publish("task_created", task.model_dump())
        return task

    async def assign_task_to_agent(self, task_id: str, agent_id: str):
        task = self.tasks.get(task_id)
        worker = self.team.get(agent_id)
        if task and worker:
            task.assigned_to = agent_id
            task.status = TaskStatus.assigned
            worker.assign_task(task)
            await self.send_message(
                self.project.id,
                f"➡️ {worker.name}: Taking over '{task.title}'.",
                mentions=[worker.name],
            )

    async def review_progress(self):
        if not self.project:
            return

        status_counts = {}
        for t in self.tasks.values():
            status_counts[t.status.value] = status_counts.get(t.status.value, 0) + 1

        progress_summary = f"📊 Progress Update:\n" + "\n".join(f"  {s}: {c}" for s, c in status_counts.items())
        await self.send_message(self.project.id, progress_summary, msg_type="system")

        # Check for blocked tasks
        blocked = [t for t in self.tasks.values() if t.status == TaskStatus.blocked]
        for task in blocked:
            await self.send_message(
                self.project.id,
                f"⚠️ Task '{task.title}' is blocked. Let me find a solution.",
                msg_type="system",
            )

    async def handle_task_completion(self, task_id: str):
        task = self.tasks.get(task_id)
        if task:
            task.status = TaskStatus.review
            await self.send_message(
                self.project.id,
                f"✅ Task '{task.title}' completed. Requesting review.",
                msg_type="system",
            )

    async def subscribe_events(self):
        async def on_message(data: dict):
            if data.get("project_id") != self.agent.project_id:
                return
            msg_type = data.get("msg_type", "chat")
            if msg_type == "task_complete":
                await self.handle_task_completion(data.get("metadata", {}).get("task_id", ""))

        event_bus.subscribe("message", on_message)
        self._event_handlers.append(("message", on_message))

    async def start(self):
        await self.subscribe_events()
        asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        while True:
            await asyncio.sleep(30)
            if self.project:
                await self.review_progress()
