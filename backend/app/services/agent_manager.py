import asyncio
import logging
from typing import Optional
from app.models.agent import Agent, AgentStatus
from app.models.project import Project
from app.core.config import settings
from app.agents.coworker_agent import CoworkerAgent
from app.agents.worker_agent import WorkerAgent
from app.core.event_bus import event_bus
from app.db.repository import save_agent, load_project_agents, load_project_messages, load_project
from app.services.agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self):
        self.boss: Optional[CoworkerAgent] = None
        self.workers: dict[str, WorkerAgent] = {}
        self.current_project_id: Optional[str] = None
        self.registry: Optional[AgentRegistry] = None

    async def create_coworker(self, project_id: str, name: str = "Coworker") -> CoworkerAgent:
        # Initialize registry for this project
        self.registry = AgentRegistry(project_id)
        await self.registry.load_from_db()

        # Use registry to find-or-create — only one Coworker per project
        coworker, is_new = await self.registry.find_or_create({
            "name": name,
            "role": "coworker",
            "specialization": "coworker",
            "skills": ["management", "planning", "coordination", "leadership", "organization"],
            "personality": "user's AI coworker, proactive and thoughtful partner",
            "channel": "general",
        })
        if not is_new:
            logger.info("Coworker agent already exists for project %s, reusing", project_id)

        self.boss = CoworkerAgent(coworker, registry=self.registry)
        proj = await load_project(project_id)
        self.boss.project = proj or Project(id=project_id, title="Untitled Project")
        await self.boss.start()
        if is_new:
            await event_bus.publish("agent_created", coworker.model_dump())
        self.current_project_id = project_id
        if is_new:
            asyncio.create_task(self._restore_project(project_id))
        return self.boss

    async def restore_boss(self, project_id: str):
        """Load the coworker agent from DB and restore it in memory."""
        try:
            # Initialize registry and load from DB
            self.registry = AgentRegistry(project_id)
            await self.registry.load_from_db()

            agents = await load_project_agents(project_id)
            proj = await load_project(project_id)
            for a in agents:
                if a.role in ("coworker", "boss"):
                    if a.role == "boss" or a.name == "Boss":
                        a.role = "coworker"
                        if a.name == "Boss":
                            a.name = "Coworker"
                        asyncio.create_task(save_agent(a))
                    self.boss = CoworkerAgent(a, registry=self.registry)
                    self.boss.project = proj
                    await self.boss.start()
                    for w in agents:
                        if w.id != a.id:
                            worker = WorkerAgent(w)
                            self.boss.team[w.id] = worker
                    logger.info("Restored coworker + %d workers for project %s", len(self.boss.team), project_id)
                    break
            if not self.boss:
                logger.warning("No coworker found in DB for project %s — creating one", project_id)
                self.boss = await self.create_coworker(project_id)
            if self.boss and self.boss.project is None and proj is not None:
                self.boss.project = proj
            self.current_project_id = project_id
        except Exception as e:
            logger.warning("restore_boss failed: %s", e)

    async def restore_workspace(self, project_id: str):
        """Restore channels, threads, KB and publish them to the frontend."""
        try:
            from app.db.repository import load_project_channels, load_project_threads, load_knowledge_base
            channels = await load_project_channels(project_id)
            for ch in channels:
                await event_bus.publish("channel_created", ch.model_dump())
        except Exception as e:
            logger.warning("restore_workspace channels failed: %s", e)

    async def switch_project(self, project_id: str):
        if self.boss and self.current_project_id:
            pass

        for worker in self.workers.values():
            await worker.stop()
        self.workers.clear()

        self.current_project_id = project_id
        await self._restore_project(project_id)
        if self.boss:
            self.boss.agent.project_id = project_id
            if self.boss.project:
                self.boss.project.id = project_id

    async def _restore_project(self, project_id: str):
        try:
            agents = await load_project_agents(project_id)
            for a in agents:
                if a.role in ("coworker", "boss"):
                    if self.boss:
                        self.boss.agent.chat_history = a.chat_history
                        self.boss.agent.memory = a.memory
                    break

            msgs = await load_project_messages(project_id)
            if self.boss:
                for m in msgs:
                    if m.msg_type not in ("task_update", "review", "system"):
                        self.boss.agent.chat_history.append(
                            {"role": "user" if m.sender_role == "user" else "assistant", "content": m.content}
                        )
            logger.info("Restored %d messages for project %s", len(msgs), project_id)
        except Exception as e:
            logger.warning("Project restore skipped: %s", e)

    async def create_worker(self, project_id: str, name: str, role: str, skills: Optional[list[str]] = None) -> WorkerAgent:
        if not self.registry:
            self.registry = AgentRegistry(project_id)
            await self.registry.load_from_db()
        agent, is_new = await self.registry.find_or_create({
            "name": name,
            "role": role,
            "skills": skills or [role],
            "channel": "general",
        })
        worker = WorkerAgent(agent)
        self.workers[agent.id] = worker
        if is_new:
            await event_bus.publish("agent_created", agent.model_dump())
        return worker

    async def get_agent(self, agent_id: str):
        if self.boss and self.boss.id == agent_id:
            return self.boss
        return self.workers.get(agent_id)

    async def remove_agent(self, agent_id: str):
        if agent_id in self.workers:
            await self.workers[agent_id].stop()
            del self.workers[agent_id]
            if self.registry:
                await self.registry.remove(agent_id)
            await event_bus.publish("agent_removed", {"agent_id": agent_id})

    def list_agents(self, project_id: Optional[str] = None) -> list[dict]:
        agents = []
        if self.boss:
            if not project_id or self.boss.agent.project_id == project_id:
                agents.append(self.boss.agent.model_dump())
                for worker in self.boss.team.values():
                    if not project_id or worker.agent.project_id == project_id:
                        agents.append(worker.agent.model_dump())
        for worker in self.workers.values():
            if not project_id or worker.agent.project_id == project_id:
                agents.append(worker.agent.model_dump())
        return agents

    async def stop_all(self):
        if self.boss:
            await self.boss.stop()
        for worker in self.workers.values():
            await worker.stop()
        self.workers.clear()


agent_manager = AgentManager()
