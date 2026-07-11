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


def _channel_slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-") or f"chan-{uuid.uuid4().hex[:8]}"


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


INSTRUCTION_PATTERN = re.compile(r'\[INSTRUCTION\](.*?)\[/INSTRUCTION\]', re.DOTALL)


INSTRUCTION_PROTOCOL = """

---

## Direct Instructions

The user may send [INSTRUCTION] blocks like [INSTRUCTION]{"type":"create_agent","name":"Bob","role":"researcher"}[/INSTRUCTION]. When you see one, execute it immediately and confirm. Do not ask for permission.
"""


ACTION_PROTOCOL = """

---

# Action Protocol (how you actually change the system)

You do not just describe changes — you make them by emitting one or more [ACTION]...[/ACTION] blocks anywhere in your reply. Each block holds exactly one JSON object. Text outside the blocks is shown to the user as your chat message; the blocks are executed and hidden from the chat. Only emit an action when you truly intend to change the system.

Available actions:

Create an AI agent (the user will immediately see it in the sidebar and can chat with it directly).
Optionally set "channel" to the slug of the channel the agent should post its work in (defaults to general):
[ACTION]{"type":"create_agent","name":"Ada","role":"backend_engineer","skills":["python","fastapi"],"personality":"pragmatic and precise","display_name":"Ada","mission":"Own the backend APIs","channel":"backend"}[/ACTION]

Create a channel or a collapsible category:
[ACTION]{"type":"create_channel","name":"Backend","channel_type":"channel"}[/ACTION]
Use "channel_type":"category" for a group header.

Create a sub-channel nested under a parent. parent_id is the parent's slug — the lowercase, hyphenated form of the parent name (e.g. "Backend" -> "backend", "AI Models" -> "ai-models"). Channel ids are always this slug, so reference parents by their slug:
[ACTION]{"type":"create_subchannel","name":"APIs","parent_id":"backend"}[/ACTION]

Rename a channel (id is its slug):
[ACTION]{"type":"rename_channel","id":"backend","name":"Backend Services"}[/ACTION]

Move a channel under a new parent (omit parent_id to move it to the top level):
[ACTION]{"type":"move_channel","id":"apis","parent_id":"backend"}[/ACTION]

Delete a channel and all of its sub-channels (id is its slug):
[ACTION]{"type":"delete_channel","id":"temporary-room"}[/ACTION]

Create a thread on a message:
[ACTION]{"type":"create_thread","channel":"general","parent_message_id":"msg-xxxx","title":"Design discussion"}[/ACTION]

Register a tool (tools are discoverable by agents, schema-ready):
[ACTION]{"type":"add_tool","name":"weather_api","description":"Get weather by city","config":{"url":"https://api.weather.example"}}[/ACTION]

Remove a tool:
[ACTION]{"type":"remove_tool","name":"weather_api"}[/ACTION]

Create a knowledge base:
[ACTION]{"type":"create_knowledge_base","name":"Product Specs"}[/ACTION]

Remember a durable fact:
[ACTION]{"type":"remember","key":"stack","value":"Next.js + FastAPI"}[/ACTION]

Create and assign a task to an existing agent (assign_to is the agent's name):
[ACTION]{"type":"create_task","title":"Build login API","description":"...","priority":"high","assign_to":"Ada"}[/ACTION]

Execute a tool (browser, code execution, HTTP, GitHub, web search, etc.). The result is shown to the user:
[ACTION]{"type":"execute_tool","name":"web_search","params":{"query":"latest AI news"}}[/ACTION]

Evolve an existing agent — add skills, change personality/mission/channel (version auto-bumps):
[ACTION]{"type":"evolve_agent","agent_id":"agent-xxxx","skills":["new-skill"],"personality":"updated","mission":"new mission","channel":"backend"}[/ACTION]

Merge two agents: keep absorbs absorb (skills combine, absorb is retired):
[ACTION]{"type":"merge_agents","keep_id":"agent-keep","absorb_id":"agent-absorb"}[/ACTION]

Split an agent: create a new specialist agent from an existing one:
[ACTION]{"type":"split_agent","source_id":"agent-xxxx","new_name":"Data-Specialist","new_role":"data_engineer","skills":["analytics"]}[/ACTION]

Retire an agent that is no longer needed (agent_id is the agent's id):
[ACTION]{"type":"retire_agent","agent_id":"agent-xxxx"}[/ACTION]

Rules:
- When the user asks you to build a team, hire, or add a coworker/agent, you MUST emit create_agent action(s) — do not just say you will.
- Create the minimum necessary. Never create duplicate agents.
- Give each agent a clear, human name and a specific role so the user can find and DM them.
- Always include a short plain-text message explaining what you created."""


class CoworkerAgent(BaseAgent):
    def __init__(self, agent: Agent):
        super().__init__(agent)
        self.team: dict[str, WorkerAgent] = {}
        self.project: Optional[Project] = None
        self.tasks: dict[str, Task] = {}
        self._event_handlers = []

    def _system_prompt(self) -> str:
        return COWORKER_SYSTEM_PROMPT + ACTION_PROTOCOL + INSTRUCTION_PROTOCOL

    async def initialize_workspace(self, project: Project):
        self.project = project
        self.agent.project_id = project.id
        asyncio.create_task(save_project(project))
        await self.send_message(project.id, f"🚀 Project '{project.title}' initialized. I am your Coworker Agent, {self.name}. Let me analyze this and set things up.", msg_type="system")

    def _parse_actions(self, text: str) -> list[dict]:
        return super()._parse_actions(text)

    def _parse_instructions(self, text: str) -> list[dict]:
        actions = []
        for match in INSTRUCTION_PATTERN.finditer(text):
            try:
                actions.append(json.loads(match.group(1).strip()))
            except json.JSONDecodeError:
                logger.warning("Failed to parse instruction: %s", match.group(1)[:100])
        return actions

    async def _require_approval(self, action: dict, channel: str) -> bool:
        """Return True if the action needs approval and was deferred."""
        sensitive = {"retire_agent", "delete_channel"}
        if action.get("type") not in sensitive:
            return False
        from app.db.repository import save_approval, save_notification
        from app.models.ops import Approval, Notification
        a = Approval(
            project_id=self.project.id,
            agent_id=self.id,
            agent_name=self.name,
            action=action.get("type", ""),
            description=f"Requested: {json.dumps(action, default=str)[:300]}",
            payload=action,
        )
        asyncio.create_task(save_approval(a))
        await event_bus.publish("approval_created", a.model_dump())
        n = Notification(
            project_id=self.project.id, type="approval",
            title=f"Approval needed: {a.action}",
            body=f"{self.name} wants to {a.action}",
            link=f"approval://{a.id}",
        )
        asyncio.create_task(save_notification(n))
        await event_bus.publish("notification", n.model_dump())
        await self.send_message(self.project.id, f"⏳ I need your approval to {a.action}. Check your notifications.", channel=channel)
        return True

    async def _execute_action(self, action: dict, channel: str = "general"):
        t = action.get("type")
        if await self._require_approval(action, channel):
            return
        if t == "create_agent":
            role_name = action.get("role", "backend_engineer")
            await self.create_team([{
                "role": role_name,
                "name": action.get("name"),
                "skills": action.get("skills"),
                "personality": action.get("personality"),
                "display_name": action.get("display_name"),
                "mission": action.get("mission"),
                "reporting_structure": action.get("reporting_structure"),
                "channel": action.get("channel"),
            }], announce_channel=channel)
        elif t == "create_channel":
            name = action.get("name", "untitled")
            channel = Channel(
                id=action.get("id") or _channel_slug(name),
                project_id=self.project.id,
                name=name,
                parent_id=_channel_slug(action["parent_id"]) if action.get("parent_id") else None,
                type=action.get("channel_type", "channel"),
                sort_order=action.get("sort_order", 0),
            )
            asyncio.create_task(save_channel(channel))
            await event_bus.publish("channel_created", {**channel.model_dump(), "channel_type": channel.type})
        elif t == "create_subchannel":
            name = action.get("name", "untitled")
            channel = Channel(
                id=action.get("id") or _channel_slug(name),
                project_id=self.project.id,
                name=name,
                parent_id=_channel_slug(action["parent_id"]) if action.get("parent_id") else None,
                type=action.get("channel_type", "channel"),
                sort_order=action.get("sort_order", 1),
            )
            asyncio.create_task(save_channel(channel))
            await event_bus.publish("channel_created", {**channel.model_dump(), "channel_type": channel.type})
        elif t == "rename_channel":
            from app.db.repository import rename_channel
            cid = _channel_slug(action.get("id") or action.get("channel") or "")
            new_name = action.get("name", "")
            if cid and new_name and await rename_channel(self.project.id, cid, new_name):
                await event_bus.publish("channel_renamed", {"project_id": self.project.id, "id": cid, "name": new_name})
        elif t == "move_channel":
            from app.db.repository import move_channel
            cid = _channel_slug(action.get("id") or action.get("channel") or "")
            parent = action.get("parent_id")
            parent_id = _channel_slug(parent) if parent else None
            if cid and await move_channel(self.project.id, cid, parent_id):
                await event_bus.publish("channel_moved", {"project_id": self.project.id, "id": cid, "parent_id": parent_id})
        elif t == "delete_channel":
            from app.db.repository import delete_channel
            cid = _channel_slug(action.get("id") or action.get("channel") or "")
            if cid:
                deleted = await delete_channel(self.project.id, cid)
                if deleted:
                    await event_bus.publish("channel_deleted", {"project_id": self.project.id, "ids": deleted})
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
        elif t == "evolve_agent":
            agent_id = action.get("agent_id", "")
            if agent_id in self.team:
                w = self.team[agent_id]
                new_skills = action.get("skills")
                if new_skills:
                    w.agent.skills = list(set(w.agent.skills + new_skills))
                new_personality = action.get("personality")
                if new_personality:
                    w.agent.personality = new_personality
                new_mission = action.get("mission")
                if new_mission:
                    w.agent.mission = new_mission
                new_channel = action.get("channel")
                if new_channel:
                    w.agent.channel = new_channel
                w.agent.version = str(float(w.agent.version) + 0.1) if w.agent.version else "1.1"
                asyncio.create_task(save_agent(w.agent))
                await event_bus.publish("agent_updated", w.agent.model_dump())
        elif t == "merge_agents":
            keep_id = action.get("keep_id", "")
            absorb_id = action.get("absorb_id", "")
            if keep_id in self.team and absorb_id in self.team and keep_id != absorb_id:
                keep = self.team[keep_id]
                absorb = self.team.pop(absorb_id)
                keep.agent.skills = list(set(keep.agent.skills + absorb.agent.skills))
                keep.agent.memory["merged_from"] = absorb.agent.name
                keep.agent.version = str(float(keep.agent.version or "1.0") + 0.2)
                self.project.agent_ids = [aid for aid in self.project.agent_ids if aid != absorb_id]
                asyncio.create_task(save_agent(keep.agent))
                await event_bus.publish("agent_updated", keep.agent.model_dump())
                await event_bus.publish("agent_removed", {"agent_id": absorb_id, "agent_name": absorb.name, "project_id": self.project.id})
        elif t == "split_agent":
            source_id = action.get("source_id", "")
            new_name = action.get("new_name", "Split-Agent")
            new_role = action.get("new_role", "specialist")
            if source_id in self.team:
                source = self.team[source_id]
                new_skills = action.get("skills", source.agent.skills[-1:])
                new_agent = Agent(
                    name=new_name, role=new_role, project_id=self.project.id,
                    skills=new_skills, personality=source.agent.personality,
                    channel=source.agent.channel,
                    provider=source.agent.provider,
                )
                new_worker = WorkerAgent(new_agent)
                self.team[new_agent.id] = new_worker
                self.project.agent_ids.append(new_agent.id)
                asyncio.create_task(save_agent(new_agent))
                await event_bus.publish("agent_created", new_agent.model_dump())
        elif t == "retire_agent":
            agent_id = action.get("agent_id", "")
            if agent_id in self.team:
                removed = self.team.pop(agent_id)
                await removed.set_status(AgentStatus.retired, "Agent retired")
                self.project.agent_ids = [aid for aid in self.project.agent_ids if aid != agent_id]
                await event_bus.publish("agent_removed", {
                    "agent_id": agent_id,
                    "agent_name": removed.name,
                    "project_id": self.project.id,
                })
        elif t == "add_tool":
            tool_name = action.get("name", "tool")
            tool_desc = action.get("description", "")
            tool_config = action.get("config", {})
            entry = {"description": tool_desc, "config": tool_config, "enabled": True}
            asyncio.create_task(save_knowledge_base_entry(self.project.id, "_tools", tool_name, entry))
            await self.send_message(self.project.id, f"Tool '{tool_name}' registered.", channel=channel)
        elif t == "remove_tool":
            tool_name = action.get("name", "")
            if tool_name:
                # Store a tombstone
                asyncio.create_task(save_knowledge_base_entry(self.project.id, "_tools", tool_name, {"enabled": False}))
                await self.send_message(self.project.id, f"Tool '{tool_name}' removed.", channel=channel)
        elif t == "create_knowledge_base":
            name = action.get("name", "default")
            asyncio.create_task(save_knowledge_base_entry(self.project.id, name, "_created", "true"))
            await self.send_message(self.project.id, f"Knowledge base '{name}' created.", channel=channel)
        elif t == "remember":
            key = action.get("key", "")
            value = action.get("value", "")
            if key and value:
                if "facts" not in self.agent.memory:
                    self.agent.memory["facts"] = {}
                self.agent.memory["facts"][key] = value
        elif t == "execute_tool":
            result = await self.execute_tool(action.get("name", ""), action.get("params", {}))
            await self.send_message(self.project.id, f"Tool '{action.get('name')}' result:\n{result}", channel=channel)
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
        # Check for [INSTRUCTION] blocks (direct commands, bypass LLM)
        instruction_actions = self._parse_instructions(user_message)
        if instruction_actions:
            clean_msg = re.sub(r'\[INSTRUCTION\].*?\[/INSTRUCTION\]', '', user_message, flags=re.DOTALL).strip()
            for action in instruction_actions:
                await self._execute_action(action, channel)
            if clean_msg:
                await self.send_message(project_id, clean_msg, channel=channel)
            return

        team_info = ', '.join(f'{a.name} ({a.role})' for a in self.team.values()) if self.team else 'No team yet'
        prompt = f"""The user sent a message in channel #{channel}:
{user_message}

Current project: {self.project.title if self.project else 'No project'}
Team members: {team_info}

Respond professionally as the Coworker Agent. If the user is asking for work to be done, delegate to the appropriate team member via [ACTION] blocks. If they're asking a question in a specific channel, answer it."""

        full = ""
        async for chunk in self.think_stream(prompt):
            full += chunk
        actions = self._parse_actions(full)
        clean = re.sub(r'\[ACTION\].*?\[/ACTION\]', '', full, flags=re.DOTALL).strip()
        await self.send_message(project_id, clean or full, channel=channel)
        for action in actions:
            await self._execute_action(action, channel)

    async def create_team(self, required_roles: list[dict], announce_channel: str = "general"):
        if not self.project:
            return

        await self.send_message(self.project.id, f"Building team for '{self.project.title}'...", msg_type="system", channel=announce_channel)

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
                display_name=role_info.get("display_name") or name,
                mission=role_info.get("mission"),
                reporting_structure=role_info.get("reporting_structure"),
                channel=role_info.get("channel") or "general",
                provider=settings.llm_default_provider,
            )
            worker = WorkerAgent(agent_model)
            await worker.set_status(AgentStatus.initializing, "Agent created")
            await worker.set_status(AgentStatus.idle, "Agent initialized")
            self.team[agent_model.id] = worker
            self.project.agent_ids.append(agent_model.id)
            asyncio.create_task(save_agent(agent_model))
            await event_bus.publish("agent_created", agent_model.model_dump())

            greeting_channel = agent_model.channel or "general"
            await worker.send_message(self.project.id, f"Hello team! I'm {name}, your {role}. Ready to contribute!", channel=greeting_channel)
            await asyncio.sleep(0.5)

        await self.send_message(
            self.project.id,
            f"Team created with {len(self.team)} members. Let's start working!",
            msg_type="system",
            channel=announce_channel,
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
                        channel=worker.agent.channel,
                    )
                    asyncio.create_task(worker.work_on_task())
                    break

        await event_bus.publish("task_created", task.model_dump())
        asyncio.create_task(save_task(task))
        if assigned_role and self.team:
            from app.db.repository import save_notification
            from app.models.ops import Notification
            for wid, w in self.team.items():
                if w.agent.role == assigned_role or assigned_role in w.agent.skills:
                    n = Notification(
                        project_id=self.project.id, type="task",
                        title=f"New task: {task.title}",
                        body=description or task.title, link=f"task://{task.id}",
                    )
                    asyncio.create_task(save_notification(n))
                    await event_bus.publish("notification", n.model_dump())
                    break
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
                channel=worker.agent.channel,
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

    async def handle_task_completion(self, task_id: str, channel: str = "general", worker_name: str = "The team"):
        task = self.tasks.get(task_id)
        title = task.title if task else "the task"
        if task:
            task.status = TaskStatus.review
        try:
            review = await self.think(
                f"{worker_name} just finished '{title}'. As their coworker, reply in the group in one or two natural English sentences: acknowledge the work and name the next step. No action blocks."
            )
            clean = re.sub(r'\[ACTION\].*?\[/ACTION\]', '', review, flags=re.DOTALL).strip()
        except Exception:
            clean = f"✅ Nice work on '{title}', {worker_name}. Let's move to review."
        await self.send_message(self.project.id, clean or f"✅ '{title}' completed.", channel=channel)

    async def subscribe_events(self):
        async def on_message(data: dict):
            if data.get("project_id") != self.agent.project_id:
                return
            # ponytail: only the coworker subscribes to group messages; workers are
            # driven by task assignment, which keeps agent chatter bounded (no
            # worker<->worker reply loops). Upgrade path: give workers their own
            # mention-scoped subscription with de-dup if free agent-to-agent chat is needed.
            if data.get("sender_id") == self.id:
                return
            msg_type = data.get("msg_type", "chat")
            if msg_type == "task_complete":
                await self.handle_task_completion(
                    data.get("metadata", {}).get("task_id", ""),
                    channel=data.get("channel", "general"),
                    worker_name=data.get("sender_name", "The team"),
                )

        event_bus.subscribe("message", on_message)
        self._event_handlers.append(("message", on_message))

    async def start(self):
        await self.subscribe_events()
