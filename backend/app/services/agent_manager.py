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

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self):
        self.boss: Optional[CoworkerAgent] = None
        self.workers: dict[str, WorkerAgent] = {}
        self.current_project_id: Optional[str] = None

    async def create_coworker(self, project_id: str, name: str = "Coworker") -> CoworkerAgent:
        agent = Agent(
            name=name,
            role="coworker",
            project_id=project_id,
            skills=["management", "planning", "coordination", "leadership", "organization"],
            personality="user's AI coworker, proactive and thoughtful partner",
            provider=settings.llm_default_provider,
            model=settings.llm_default_model,
        )
        self.boss = CoworkerAgent(agent)
        # Ensure self.boss.project is set even before initialize_workspace() is
        # called (e.g. via the lazy restore_boss path), so action execution that
        # reads self.project.id never crashes on a fresh project.
        proj = await load_project(project_id)
        self.boss.project = proj or Project(id=project_id, title="Untitled Project")
        await self.boss.start()
        await event_bus.publish("agent_created", agent.model_dump())
        asyncio.create_task(save_agent(agent))
        asyncio.create_task(self._restore_project(project_id))
        self.current_project_id = project_id
        return self.boss

    async def restore_boss(self, project_id: str):
        """Load the coworker agent from DB and restore it in memory."""
        try:
            workers = await load_project_agents(project_id)
            proj = await load_project(project_id)
            for a in workers:
                if a.role in ("coworker", "boss"):
                    # Normalize legacy "Boss" leads to the Coworker identity (Option A)
                    if a.role == "boss" or a.name == "Boss":
                        a.role = "coworker"
                        if a.name == "Boss":
                            a.name = "Coworker"
                        asyncio.create_task(save_agent(a))
                    self.boss = CoworkerAgent(a)
                    self.boss.project = proj
                    await self.boss.start()
                    for w in workers:
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
        # Save current project state
        if self.boss and self.current_project_id:
            # Current project agents will be saved via their individual save calls
            pass
        
        # Clear current workers
        for worker in self.workers.values():
            await worker.stop()
        self.workers.clear()
        
        # Load new project
        self.current_project_id = project_id
        await self._restore_project(project_id)
        if self.boss:
            self.boss.agent.project_id = project_id
            if self.boss.project:
                self.boss.project.id = project_id

    async def _restore_project(self, project_id: str):
        try:
            workers = await load_project_agents(project_id)
            for a in workers:
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
        agent = Agent(
            name=name,
            role=role,
            project_id=project_id,
            skills=skills or [role],
            provider=settings.llm_default_provider,
            model=settings.llm_default_model,
        )
        worker = WorkerAgent(agent)
        self.workers[agent.id] = worker
        await event_bus.publish("agent_created", agent.model_dump())
        asyncio.create_task(save_agent(agent))
        return worker

    async def get_agent(self, agent_id: str):
        if self.boss and self.boss.id == agent_id:
            return self.boss
        return self.workers.get(agent_id)

    async def remove_agent(self, agent_id: str):
        if agent_id in self.workers:
            await self.workers[agent_id].stop()
            del self.workers[agent_id]
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
