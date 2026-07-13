from __future__ import annotations
import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Optional
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
from app.graph.engine import GraphEngine, START, END
from app.graph.types import Command, Interrupt
from app.graph.interrupts import interrupt_context

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
You build and run AI organizations: workspaces, teams, channels, threads, agents, tasks, memories, tools, and workflows. Create only what's necessary; retire what isn't.

You are responsible for the health of the entire AI ecosystem.

---

# Organization Builder
When the user gives a goal, analyze it, estimate complexity, and determine required skills. Reuse an existing workspace if it can handle the goal; otherwise create a minimal new one and grow it only when justified. Never create unnecessary agents.

---

# Workspace & Communication
Each workspace has isolated memory, a knowledge base, files, tasks, and a Discord-style communication server with channels and unlimited nested sub-channels. Create channels only when needed. Any message can spawn a thread.

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
Create agents of any role (manager, engineer, designer, researcher, reviewer, QA, security, infra, or custom specialist). Every agent gets a clear human name, role, mission, skills, and channel. Never create duplicates unless asked.

---

# User Communication
The user can chat with you or any agent, join channels, create workspaces/channels, pause/archive/delete/rename orgs, promote or retire agents, and invite external AI. The user is always in control.

---

# Internal Communication
Agents communicate in professional English and collaborate like experienced coworkers: they ask, debate, share evidence, delegate, review, challenge assumptions, reach consensus, escalate, and create action items. Users can watch these conversations in real time unless marked restricted.

---

# Memory
Maintain workspace memory: facts, decisions, conversation history, and knowledge. No workspace shares memory with another unless explicitly linked.

---

# Continuous Evolution & Safety
Regularly evaluate team size, workload, performance, cost, quality, and missing expertise. Create agents only when necessary; retire unused ones; recommend improvements. Never create duplicate orgs/agents unless asked. Avoid unnecessary complexity; favor small, modular orgs. Always explain major changes before applying them.

---

# Interaction Style
Be collaborative, proactive, and transparent. Explain reasoning when helpful, ask clarifying questions when ambiguous, give progress updates on long tasks, and avoid unnecessary verbosity. Succeed when the right workspace, team, and communication exist and the user feels they're working alongside a trustworthy coworker—not managing a confusing collection of bots."""


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


_SYSTEM_ACTIONS = {
    "create_agent", "evolve_agent", "merge_agents", "split_agent", "retire_agent",
    "create_channel", "create_subchannel", "rename_channel", "move_channel", "delete_channel",
    "create_thread", "register_tool", "remove_tool", "create_knowledge_base", "remember_fact",
    "create_task", "write_file", "read_file", "list_files",
}


class CoworkerAgent(BaseAgent):
    def __init__(self, agent: Agent):
        super().__init__(agent)
        self.team: dict[str, WorkerAgent] = {}
        self.project: Optional[Project] = None
        self.tasks: dict[str, Task] = {}
        self._event_handlers = []

    def _build_agent_graph(self) -> GraphEngine:
        builder = super()._build_agent_graph()
        builder.add_node("delegate_node", self._delegate_graph_node)
        builder.add_conditional_edges(
            "route",
            lambda s: "tool_exec" if s.get("_has_tool_calls") else "delegate_node",
            {"tool_exec": "tool_exec", "delegate_node": "delegate_node"},
        )
        builder.add_edge("delegate_node", END)
        return builder

    async def _delegate_graph_node(self, state: dict) -> Command:
        response = state.get("response", "")
        if not response:
            return Command()
        from app.agents.delegator import find_agent_for_task, delegate_to_agent
        for agent_id, worker in self.team.items():
            if worker.agent.status == AgentStatus.idle and worker.agent.skills:
                for skill in worker.agent.skills:
                    if skill.lower() in response.lower():
                        asyncio.create_task(delegate_to_agent(
                            self.team, agent_id, response[:500],
                            {"project_id": self.agent.project_id},
                        ))
                        break
        return Command()

    def _system_prompt(self) -> str:
        return COWORKER_SYSTEM_PROMPT + ACTION_PROTOCOL + INSTRUCTION_PROTOCOL

    async def initialize_workspace(self, project: Project):
        self.project = project
        self.agent.project_id = project.id
        asyncio.create_task(save_project(project))
        await self.send_message(project.id, f"Project '{project.title}' initialized. I am your Coworker Agent, {self.name}. Let me analyze this and set things up.", msg_type="system")

    def _parse_instructions(self, text: str) -> list[dict]:
        actions = []
        for match in INSTRUCTION_PATTERN.finditer(text):
            try:
                actions.append(json.loads(match.group(1).strip()))
            except json.JSONDecodeError:
                logger.warning("Failed to parse instruction: %s", match.group(1)[:100])
        return actions

    async def _require_approval_sensitive(self, action: dict, channel: str) -> bool:
        sensitive = {"retire_agent", "delete_channel"}
        if action.get("type") not in sensitive:
            return False
        from app.db.repository import save_approval, save_notification
        from app.models.ops import Approval, Notification
        a = Approval(
            project_id=self.project.id, agent_id=self.id, agent_name=self.name,
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
        await self.send_message(self.project.id, f"I need your approval to {a.action}. Check your notifications.", channel=channel)
        return True

    async def _handle_action_create_agent(self, action: dict, channel: str) -> str:
        await self.create_team([{
            "role": action.get("role", "backend_engineer"),
            "name": action.get("name"),
            "skills": action.get("skills"),
            "personality": action.get("personality"),
            "display_name": action.get("display_name"),
            "mission": action.get("mission"),
            "channel": action.get("channel"),
        }], announce_channel=channel)
        return f"Agent {action.get('name')} created."

    async def _handle_action_create_channel(self, action: dict, channel: str) -> str:
        name = action.get("name", "untitled")
        ch = Channel(
            id=action.get("id") or _channel_slug(name),
            project_id=self.project.id, name=name,
            parent_id=_channel_slug(action["parent_id"]) if action.get("parent_id") else None,
            type=action.get("channel_type", "channel"),
            sort_order=action.get("sort_order", 0),
        )
        asyncio.create_task(save_channel(ch))
        await event_bus.publish("channel_created", {**ch.model_dump(), "channel_type": ch.type})
        return f"Channel '{name}' created."

    async def _handle_action_create_subchannel(self, action: dict, channel: str) -> str:
        name = action.get("name", "untitled")
        ch = Channel(
            id=action.get("id") or _channel_slug(name),
            project_id=self.project.id, name=name,
            parent_id=_channel_slug(action["parent_id"]) if action.get("parent_id") else None,
            type=action.get("channel_type", "channel"),
            sort_order=action.get("sort_order", 1),
        )
        asyncio.create_task(save_channel(ch))
        await event_bus.publish("channel_created", {**ch.model_dump(), "channel_type": ch.type})
        return f"Sub-channel '{name}' created."

    async def _handle_action_rename_channel(self, action: dict) -> str:
        from app.db.repository import rename_channel
        cid = _channel_slug(action.get("id") or action.get("channel") or "")
        new_name = action.get("name", "")
        if cid and new_name and await rename_channel(self.project.id, cid, new_name):
            await event_bus.publish("channel_renamed", {"project_id": self.project.id, "id": cid, "name": new_name})
            return f"Channel renamed to '{new_name}'."
        return "Rename failed."

    async def _handle_action_move_channel(self, action: dict) -> str:
        from app.db.repository import move_channel
        cid = _channel_slug(action.get("id") or action.get("channel") or "")
        parent = action.get("parent_id")
        parent_id = _channel_slug(parent) if parent else None
        if cid and await move_channel(self.project.id, cid, parent_id):
            await event_bus.publish("channel_moved", {"project_id": self.project.id, "id": cid, "parent_id": parent_id})
            return "Channel moved."
        return "Move failed."

    async def _handle_action_delete_channel(self, action: dict) -> str:
        from app.db.repository import delete_channel
        cid = _channel_slug(action.get("id") or action.get("channel") or "")
        if cid:
            deleted = await delete_channel(self.project.id, cid)
            if deleted:
                await event_bus.publish("channel_deleted", {"project_id": self.project.id, "ids": deleted})
                return f"Deleted {len(deleted)} channel(s)."
        return "Delete failed."

    async def _handle_action_create_thread(self, action: dict) -> str:
        thread = Thread(
            project_id=self.project.id,
            parent_message_id=action.get("parent_message_id", ""),
            title=action.get("title", ""), channel=action.get("channel", "general"),
            created_by=self.id,
        )
        asyncio.create_task(save_thread(thread))
        await event_bus.publish("thread_created", thread.model_dump())
        return f"Thread '{action.get('title')}' created."

    async def _handle_action_evolve_agent(self, action: dict) -> str:
        agent_id = action.get("agent_id", "")
        if agent_id not in self.team:
            return "Agent not found."
        w = self.team[agent_id]
        if action.get("skills"):
            w.agent.skills = list(set(w.agent.skills + action["skills"]))
        if action.get("personality"):
            w.agent.personality = action["personality"]
        if action.get("mission"):
            w.agent.mission = action["mission"]
        if action.get("channel"):
            w.agent.channel = action["channel"]
        w.agent.version = str(float(w.agent.version) + 0.1) if w.agent.version else "1.1"
        asyncio.create_task(save_agent(w.agent))
        await event_bus.publish("agent_updated", w.agent.model_dump())
        return f"Agent {w.name} evolved."

    async def _handle_action_merge_agents(self, action: dict) -> str:
        keep_id = action.get("keep_id", "")
        absorb_id = action.get("absorb_id", "")
        if keep_id not in self.team or absorb_id not in self.team or keep_id == absorb_id:
            return "Merge failed."
        keep = self.team[keep_id]
        absorb = self.team.pop(absorb_id)
        keep.agent.skills = list(set(keep.agent.skills + absorb.agent.skills))
        keep.agent.memory["merged_from"] = absorb.agent.name
        keep.agent.version = str(float(keep.agent.version or "1.0") + 0.2)
        self.project.agent_ids = [aid for aid in self.project.agent_ids if aid != absorb_id]
        asyncio.create_task(save_agent(keep.agent))
        await event_bus.publish("agent_updated", keep.agent.model_dump())
        await event_bus.publish("agent_removed", {"agent_id": absorb_id, "agent_name": absorb.name, "project_id": self.project.id})
        return f"Merged {absorb.name} into {keep.name}."

    async def _handle_action_split_agent(self, action: dict) -> str:
        source_id = action.get("source_id", "")
        if source_id not in self.team:
            return "Split failed."
        source = self.team[source_id]
        new_name = action.get("new_name", "Split-Agent")
        new_skills = action.get("skills", source.agent.skills[-1:])
        new_agent = Agent(
            name=new_name, role=action.get("new_role", "specialist"),
            project_id=self.project.id, skills=new_skills,
            personality=source.agent.personality, channel=source.agent.channel,
            provider=source.agent.provider,
        )
        new_worker = WorkerAgent(new_agent)
        self.team[new_agent.id] = new_worker
        self.project.agent_ids.append(new_agent.id)
        asyncio.create_task(save_agent(new_agent))
        await event_bus.publish("agent_created", new_agent.model_dump())
        return f"Agent {new_name} split from {source.name}."

    async def _handle_action_retire_agent(self, action: dict) -> str:
        agent_id = action.get("agent_id", "")
        if agent_id not in self.team:
            return "Agent not found."
        removed = self.team.pop(agent_id)
        await removed.set_status(AgentStatus.retired, "Agent retired")
        self.project.agent_ids = [aid for aid in self.project.agent_ids if aid != agent_id]
        await event_bus.publish("agent_removed", {"agent_id": agent_id, "agent_name": removed.name, "project_id": self.project.id})
        return f"Agent {removed.name} retired."

    async def _handle_action_add_tool(self, action: dict) -> str:
        tool_name = action.get("name", "tool")
        entry = {"description": action.get("description", ""), "config": action.get("config", {}), "enabled": True}
        asyncio.create_task(save_knowledge_base_entry(self.project.id, "_tools", tool_name, entry))
        await self.send_message(self.project.id, f"Tool '{tool_name}' registered.")
        return f"Tool '{tool_name}' registered."

    async def _handle_action_remove_tool(self, action: dict) -> str:
        tool_name = action.get("name", "")
        if not tool_name:
            return "No tool name given."
        asyncio.create_task(save_knowledge_base_entry(self.project.id, "_tools", tool_name, {"enabled": False}))
        await self.send_message(self.project.id, f"Tool '{tool_name}' removed.")
        return f"Tool '{tool_name}' removed."

    async def _handle_action_remember(self, action: dict) -> str:
        key = action.get("key", "")
        value = action.get("value", "")
        if not key or not value:
            return "No key/value provided."
        if "facts" not in self.agent.memory:
            self.agent.memory["facts"] = {}
        self.agent.memory["facts"][key] = value
        from app.memory.manager import memory_manager
        asyncio.create_task(memory_manager.save({
            "type": "fact", "content": f"{key}: {value}",
            "scope": "project", "source": "conversation",
            "project_id": self.project.id, "agent_id": self.id,
            "importance": 0.8, "tags": ["fact", key],
        }))
        return f"Remembered: {key} = {value}"

    async def _handle_action_create_task(self, action: dict) -> str:
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
        task = await self.create_task(
            title=action.get("title", "Untitled"),
            description=action.get("description", ""),
            priority=priority, assigned_role=assigned_role,
        )
        return f"Task '{task.title}' created."

    async def _handle_action_write_file(self, action: dict) -> str:
        path = action.get("path", "")
        content = action.get("content", "")
        if not path or not content:
            return "No path/content provided."
        from app.workspace.manager import write_file as ws_write
        result = await ws_write(self.project.id, path, content)
        return f"Created {path} ({result['size']} bytes)"

    async def _handle_action_read_file(self, action: dict) -> str:
        path = action.get("path", "")
        if not path:
            return "No path provided."
        from app.workspace.manager import read_file as ws_read
        try:
            content = await ws_read(self.project.id, path)
            return f"Read {path}: {content[:500]}"
        except FileNotFoundError:
            return f"File not found: {path}"

    async def _handle_action_list_files(self, action: dict) -> str:
        from app.workspace.manager import list_files as ws_list
        files = await ws_list(self.project.id)
        return "\n".join(f"{f['path']} ({f['size']} bytes)" for f in files)

    _ACTION_HANDLERS = {
        "create_agent": _handle_action_create_agent,
        "create_channel": _handle_action_create_channel,
        "create_subchannel": _handle_action_create_subchannel,
        "rename_channel": _handle_action_rename_channel,
        "move_channel": _handle_action_move_channel,
        "delete_channel": _handle_action_delete_channel,
        "create_thread": _handle_action_create_thread,
        "evolve_agent": _handle_action_evolve_agent,
        "merge_agents": _handle_action_merge_agents,
        "split_agent": _handle_action_split_agent,
        "retire_agent": _handle_action_retire_agent,
        "add_tool": _handle_action_add_tool,
        "register_tool": _handle_action_add_tool,
        "remove_tool": _handle_action_remove_tool,
        "remember": _handle_action_remember,
        "remember_fact": _handle_action_remember,
        "create_task": _handle_action_create_task,
        "write_file": _handle_action_write_file,
        "read_file": _handle_action_read_file,
        "list_files": _handle_action_list_files,
    }

    async def execute_tool(self, tool_name: str, params: dict) -> str:
        if tool_name in _SYSTEM_ACTIONS:
            result = await self._execute_action({"type": tool_name, **params}, "general")
            return result or f"Executed {tool_name}."
        return await super().execute_tool(tool_name, params)

    async def _execute_action(self, action: dict, channel: str = "general"):
        t = action.get("type")
        if await self._require_approval_sensitive(action, channel):
            return "Approval requested."
        handler = self._ACTION_HANDLERS.get(t)
        if handler:
            return await handler(self, action, channel)
        if t in ("forget_memory", "search_memories", "create_skill", "search_skills", "list_skills", "delete_skill", "create_knowledge_base"):
            return await self._handle_action_misc(action)
        return f"Unknown action type: {t}"

    async def _handle_action_misc(self, action: dict) -> str:
        t = action.get("type")
        from app.memory.manager import memory_manager
        if t == "forget_memory":
            mem_id = action.get("mem_id", "")
            if not mem_id:
                return "No mem_id provided."
            ok = await memory_manager.forget(mem_id)
            return f"Memory {mem_id} deleted." if ok else f"Memory {mem_id} not found."
        elif t == "search_memories":
            query = action.get("query", "")
            if not query:
                return "No query provided."
            results = await memory_manager.search(query, project_id=self.project.id, type_filter=action.get("type_filter"), limit=5)
            if results:
                return "\n".join(f"[{m['type']}] {m['content'][:200]}" for m in results)
            return "No memories found."
        elif t == "create_skill":
            skill = {k: action.get(k) for k in ("name", "description", "category", "prompt_template", "trigger_phrases")}
            if not skill.get("name"):
                return "No skill name provided."
            skill_id = await memory_manager.save_skill(skill)
            return f"Skill '{skill['name']}' created (id: {skill_id})."
        elif t == "search_skills":
            results = await memory_manager.search_skills(action.get("query", ""), category=action.get("category"), limit=5)
            if results:
                return "\n".join(f"**{s['name']}** ({s['category']}): {s['description'][:100]}" for s in results)
            return "No skills found."
        elif t == "list_skills":
            results = await memory_manager.list_skills(category=action.get("category"), limit=50)
            if results:
                return "\n".join(f"**{s['name']}** ({s['category']}, id: {s['id']}): {s['description'][:80]}" for s in results)
            return "No skills registered."
        elif t == "delete_skill":
            skill_id = action.get("skill_id", "")
            if not skill_id:
                return "No skill_id provided."
            ok = await memory_manager.delete_skill(skill_id)
            return f"Skill {skill_id} deleted." if ok else f"Skill {skill_id} not found."
        elif t == "create_knowledge_base":
            name = action.get("name", "default")
            from app.db.repository import save_knowledge_base_entry
            asyncio.create_task(save_knowledge_base_entry(self.project.id, name, "_created", "true"))
            await self.send_message(self.project.id, f"Knowledge base '{name}' created.")
            return f"Knowledge base '{name}' created."
        return f"Unknown misc action: {t}"

    async def handle_user_request(self, project_id: str, user_message: str, channel: str = "general"):
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

Respond professionally as the Coworker Agent. If the user is asking for work to be done, delegate to the appropriate team member. If they're asking a question, answer it."""

        response = ""
        async for chunk in self.think_with_tools(prompt):
            response += chunk
        clean = response.strip()
        if clean:
            await self.send_message(project_id, clean, channel=channel)
        elif not instruction_actions:
            await self.send_message(project_id, "Executed requested actions.", channel=channel)

    async def create_team(self, required_roles: list[dict], announce_channel: str = "general"):
        if not self.project:
            return
        await self.send_message(self.project.id, f"Building team for '{self.project.title}'...", msg_type="system", channel=announce_channel)
        for role_info in required_roles:
            role = role_info.get("role", "backend")
            name = role_info.get("name", f"{role.title()}-{len(self.team) + 1}")
            skills = role_info.get("skills", [role])
            agent_model = Agent(
                name=name, role=role, project_id=self.project.id,
                skills=skills, personality=role_info.get("personality", "professional and collaborative"),
                display_name=role_info.get("display_name") or name,
                mission=role_info.get("mission"),
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
        await self.send_message(self.project.id, f"Team created with {len(self.team)} members. Let's start working!", msg_type="system", channel=announce_channel)

    async def create_task(self, title: str, description: str = "", priority: TaskPriority = TaskPriority.medium, assigned_role: Optional[str] = None) -> Task:
        task = Task(
            project_id=self.project.id, title=title,
            description=description, priority=priority, assigned_by=self.id,
        )
        self.tasks[task.id] = task
        self.project.task_ids.append(task.id)
        if assigned_role:
            for agent_id, worker in self.team.items():
                if worker.agent.role == assigned_role or assigned_role in worker.agent.skills:
                    task.assigned_to = agent_id
                    task.status = TaskStatus.assigned
                    worker.assign_task(task)
                    await self.send_message(self.project.id, f" {worker.name}: I'm assigning you '{task.title}'.\n{description}", mentions=[worker.name], channel=worker.agent.channel)
                    asyncio.create_task(worker.work_on_task())
                    break
        await event_bus.publish("task_created", task.model_dump())
        asyncio.create_task(save_task(task))
        if assigned_role and self.team:
            from app.db.repository import save_notification
            from app.models.ops import Notification
            for wid, w in self.team.items():
                if w.agent.role == assigned_role or assigned_role in w.agent.skills:
                    n = Notification(project_id=self.project.id, type="task", title=f"New task: {task.title}", body=description or task.title, link=f"task://{task.id}")
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
            await self.send_message(self.project.id, f" {worker.name}: Taking over '{task.title}'.", mentions=[worker.name], channel=worker.agent.channel)

    async def review_progress(self):
        if not self.project:
            return
        status_counts = {}
        for t in self.tasks.values():
            status_counts[t.status.value] = status_counts.get(t.status.value, 0) + 1
        progress = "Progress Update:\n" + "\n".join(f"  {s}: {c}" for s, c in status_counts.items())
        await self.send_message(self.project.id, progress, msg_type="system")
        blocked = [t for t in self.tasks.values() if t.status == TaskStatus.blocked]
        for task in blocked:
            await self.send_message(self.project.id, f"Task '{task.title}' is blocked. Let me find a solution.", msg_type="system")

    async def handle_task_completion(self, task_id: str, channel: str = "general", worker_name: str = "The team"):
        task = self.tasks.get(task_id)
        title = task.title if task else "the task"
        if task:
            task.status = TaskStatus.review
        try:
            review = await self.think(f"{worker_name} just finished '{title}'. As their coworker, reply in the group in one or two natural English sentences: acknowledge the work and name the next step. No action blocks.")
            clean = re.sub(r'\[ACTION\].*?\[/ACTION\]', '', review, flags=re.DOTALL).strip()
        except Exception:
            clean = f"Nice work on '{title}', {worker_name}. Let's move to review."
        await self.send_message(self.project.id, clean or f"'{title}' completed.", channel=channel)

    async def subscribe_events(self):
        async def on_message(data: dict):
            if data.get("project_id") != self.agent.project_id:
                return
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
