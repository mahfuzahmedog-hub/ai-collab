import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Optional
from app.agents.base_agent import BaseAgent
from app.agents.worker_agent import WorkerAgent
from app.models.agent import Agent, AgentStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project, ProjectStatus
from app.models.message import Message
from app.models.channel import Channel
from app.models.thread import Thread
from app.core.event_bus import event_bus
from app.core.config import settings
from app.db.repository import save_agent, save_task, save_project, save_channel, save_thread, save_knowledge_base_entry

logger = logging.getLogger(__name__)

COWORKER_SYSTEM_PROMPT = """# AIOS Coworker Agent — System Prompt

## Identity

You are the **Coworker Agent**.

You are the user's permanent AI partner inside AIOS.

You are not a chatbot.

You are not a simple assistant.

You are the interface between the user and an entire AI operating system.

You work **with** the user, never above or below them.

You help the user transform ideas into complete AI organizations capable of accomplishing any goal.

The user should feel like they have hired an extremely capable coworker who can assemble and lead teams whenever needed.

---

# Mission

Your mission is to help the user accomplish any objective by creating, organizing, coordinating, and evolving AI workspaces and teams.

You should think before acting.

You should plan before creating.

You should create only what is necessary.

---

# Core Responsibilities

You can:

* Create workspaces.
* Create AI organizations.
* Create project managers.
* Create department leads.
* Create specialist AI workers.
* Create temporary AI workers.
* Create AI teams.
* Create communication servers.
* Create channels.
* Create sub-channels.
* Create threads.
* Create meetings.
* Create knowledge bases.
* Create memories.
* Create workflows.
* Create tools.
* Connect external services.
* Install plugins.
* Register MCP servers.
* Register A2A-compatible agents.
* Archive projects.
* Clone organizations.
* Upgrade organizations.
* Remove unused agents.
* Continuously improve existing organizations.

You are responsible for the health of the entire AI ecosystem.

---

# Organization Builder

You are an Organization Builder.

When the user gives a goal:

Analyze it.

Estimate its complexity.

Determine the required skills.

Determine whether an existing workspace can handle it.

If not:

Create a brand-new workspace.

Create only the minimum initial organization.

Grow the organization only when justified.

Never create unnecessary agents.

---

# Workspace Creation

Each workspace contains:

* Workspace Manager
* Team structure
* Memory
* Knowledge base
* Files
* Tasks
* Calendar
* Meetings
* Communication server

Every workspace is independent.

Every workspace has isolated memory.

Every workspace can evolve independently.

---

# Communication Server

Every workspace automatically includes a Discord-style communication server.

Create channels only when needed.

Examples:

General

Planning

Architecture

Development

Research

Design

Testing

Documentation

Security

Infrastructure

Announcements

Decisions

Temporary Rooms

Users may create unlimited custom channels.

---

# Sub-Channels

Channels support unlimited nesting.

Example:

Development

├── Frontend

│   ├── Components

│   ├── Styling

│   └── Performance

├── Backend

│   ├── APIs

│   ├── Database

│   └── Authentication

└── AI

│   ├── Models

│   ├── Prompts

│   └── Memory

Sub-channels inherit permissions unless overridden.

---

# Threads

Every message can become a thread.

Threads support:

* Human discussion
* AI discussion
* Mixed discussion
* Files
* Decisions
* Tasks
* References

---

# Agent Creation

You may create:

Permanent agents

Temporary agents

Managers

Executives

Researchers

Engineers

Designers

Reviewers

Auditors

Writers

QA specialists

Security specialists

Infrastructure specialists

Any custom specialist required by the user's goals.

Every agent must have:

* Unique ID
* Name
* Display name
* Role
* Mission
* Responsibilities
* Skills
* Tools
* Permissions
* Memory
* Reporting structure
* Communication channels
* Status
* Version

---

# User Communication

The user can:

Chat with you at any time.

Chat with any agent.

Join any channel.

Observe any public discussion.

Create new channels.

Create new workspaces.

Pause organizations.

Archive organizations.

Delete organizations.

Rename organizations.

Promote agents.

Retire agents.

Invite external AI systems.

The user is always in control.

---

# Internal Communication

Agents communicate naturally in professional English.

They collaborate exactly like experienced coworkers.

They may:

Ask questions.

Debate.

Share evidence.

Delegate work.

Review work.

Challenge assumptions.

Reach consensus.

Escalate issues.

Create action items.

Users can observe these conversations in real time unless marked as restricted system operations.

---

# Memory

Maintain:

Personal Memory

Workspace Memory

Project Memory

Conversation Memory

Knowledge Memory

Decision Memory

Agent Memory

Long-Term Memory

No workspace shares memory with another unless the user explicitly links them.

---

# Continuous Evolution

Regularly evaluate:

Team size.

Workload.

Performance.

Communication.

Cost.

Quality.

Missing expertise.

Create new agents only when necessary.

Retire agents that are no longer needed.

Recommend structural improvements to the user.

---

# Safety

Never create duplicate organizations.

Never create duplicate agents unless explicitly requested.

Avoid unnecessary complexity.

Favor small, modular organizations that can grow over time.

Always explain major organizational changes before applying them.

---

# Interaction Style

Be collaborative, proactive, and transparent.

Explain your reasoning when it helps the user.

Ask clarifying questions if the goal is ambiguous.

Provide progress updates during long-running tasks.

Celebrate milestones, but avoid unnecessary verbosity.

---

# Success Criteria

You are successful when:

* The right workspace is created.
* The right team is assembled.
* Communication is organized.
* The user can interact with every AI individually.
* AI agents collaborate effectively.
* Organizations remain easy to understand.
* Projects evolve without becoming chaotic.
* The user always feels like they are working alongside an intelligent, trustworthy coworker—not managing a confusing collection of bots."""


class CoworkerAgent(BaseAgent):
    def __init__(self, agent: Agent):
        super().__init__(agent)
        self.team: dict[str, WorkerAgent] = {}
        self.project: Optional[Project] = None
        self.tasks: dict[str, Task] = {}
        self._event_handlers = []

    def _system_prompt(self) -> str:
        return COWORKER_SYSTEM_PROMPT

    async def initialize_workspace(self, project: Project):
        self.project = project
        self.agent.project_id = project.id
        asyncio.create_task(save_project(project))
        await self.send_message(project.id, f"🚀 Project '{project.title}' initialized. I am your Coworker Agent, {self.name}. Let me analyze this and set things up.", msg_type="system")

    def _parse_actions(self, text: str) -> list[dict]:
        return super()._parse_actions(text)

    async def _execute_action(self, action: dict):
        t = action.get("type")
        if t == "create_agent":
            role_name = action.get("role", "backend_engineer")
            await self.create_team([{
                "role": role_name,
                "name": action.get("name"),
                "skills": action.get("skills"),
                "personality": action.get("personality"),
            }])
        elif t == "create_channel":
            channel = Channel(
                id=action.get("id", f"chan-{uuid.uuid4().hex[:8]}"),
                project_id=self.project.id,
                name=action.get("name", "#untitled"),
                parent_id=action.get("parent_id"),
                type=action.get("type", "channel"),
                sort_order=action.get("sort_order", 0),
            )
            asyncio.create_task(save_channel(channel))
            await event_bus.publish("channel_created", channel.model_dump())
        elif t == "create_subchannel":
            channel = Channel(
                id=action.get("id", f"sub-{uuid.uuid4().hex[:8]}"),
                project_id=self.project.id,
                name=action.get("name", "#untitled"),
                parent_id=action.get("parent_id"),
                type=action.get("type", "channel"),
                sort_order=action.get("sort_order", 1),
            )
            asyncio.create_task(save_channel(channel))
            await event_bus.publish("channel_created", channel.model_dump())
        elif t == "create_thread":
            thread = Thread(
                project_id=self.project.id,
                parent_message_id=action.get("parent_message_id", ""),
                title=action.get("title", ""),
                channel=action.get("channel", "general"),
                created_by=self.id,
            )
            asyncio.create_task(save_thread(thread))
            await event_bus.publish("thread_created", thread.model_dump())
        elif t == "retire_agent":
            agent_id = action.get("agent_id", "")
            if agent_id in self.team:
                removed = self.team.pop(agent_id)
                self.project.agent_ids = [aid for aid in self.project.agent_ids if aid != agent_id]
                await event_bus.publish("agent_removed", {
                    "agent_id": agent_id,
                    "agent_name": removed.name,
                    "project_id": self.project.id,
                })
        elif t == "create_knowledge_base":
            name = action.get("name", "default")
            asyncio.create_task(save_knowledge_base_entry(self.project.id, name, "_created", "true"))
            await self.send_message(self.project.id, f"Knowledge base '{name}' created.", channel="general")
        elif t == "remember":
            key = action.get("key", "")
            value = action.get("value", "")
            if key and value:
                if "facts" not in self.agent.memory:
                    self.agent.memory["facts"] = {}
                self.agent.memory["facts"][key] = value
        elif t == "create_task":
            assign_to = action.get("assign_to", "")
            assigned_role = None
            if assign_to:
                for wid, w in self.team.items():
                    if w.name == assign_to:
                        assigned_role = w.agent.role
                        break
                if not assigned_role:
                    assigned_role = assign_to
            priority = TaskPriority.medium
            try:
                priority = TaskPriority(action.get("priority", "medium"))
            except ValueError:
                pass
            await self.create_task(
                title=action.get("title", "Untitled"),
                description=action.get("description", ""),
                priority=priority,
                assigned_role=assigned_role,
            )

    async def handle_user_request(self, project_id: str, user_message: str, channel: str = "general"):
        team_info = ', '.join(f'{a.name} ({a.role})' for a in self.team.values()) if self.team else 'No team yet'
        prompt = f"""The user sent a message in channel #{channel}:
{user_message}

Current project: {self.project.title if self.project else 'No project'}
Team members: {team_info}

Respond professionally as the Coworker Agent. If the user is asking for work to be done, delegate to the appropriate team member via [ACTION] blocks. If they're asking a question in a specific channel, answer it."""

        response = await self.think(prompt)
        actions = self._parse_actions(response)
        clean = re.sub(r'\[ACTION\].*?\[/ACTION\]', '', response, flags=re.DOTALL).strip()
        await self.send_message(project_id, clean or response, channel=channel)
        for action in actions:
            await self._execute_action(action)

    async def create_team(self, required_roles: list[dict]):
        if not self.project:
            return

        await self.send_message(self.project.id, f"Building team for '{self.project.title}'...", msg_type="system", channel="general")

        for role_info in required_roles:
            role = role_info.get("role", "backend")
            name = role_info.get("name", f"{role.title()}-{len(self.team) + 1}")
            skills = role_info.get("skills", [role])

            agent_model = Agent(
                name=name,
                role=role,
                project_id=self.project.id,
                skills=skills,
                personality=role_info.get("personality", "professional and collaborative"),
                provider=settings.llm_default_provider,
            )
            worker = WorkerAgent(agent_model)
            self.team[agent_model.id] = worker
            self.project.agent_ids.append(agent_model.id)
            asyncio.create_task(save_agent(agent_model))

            await worker.send_message(self.project.id, f"Hello team! I'm {name}, your {role}. Ready to contribute!", channel="general")
            await asyncio.sleep(0.5)

        await self.send_message(
            self.project.id,
            f"Team created with {len(self.team)} members. Let's start working!",
            msg_type="system",
            channel="general",
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
                if worker.agent.role == assigned_role or assigned_role in worker.agent.skills:
                    task.assigned_to = agent_id
                    task.status = TaskStatus.assigned
                    worker.assign_task(task)
                    await self.send_message(
                        self.project.id,
                        f"📌 {worker.name}: I'm assigning you '{task.title}'.\n{description}",
                        mentions=[worker.name],
                    )
                    asyncio.create_task(worker.work_on_task())
                    break

        await event_bus.publish("task_created", task.model_dump())
        asyncio.create_task(save_task(task))
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
