import asyncio
import logging
from typing import Optional
from app.models.agent import Agent, AgentRole, AgentStatus
from app.core.config import settings
from app.agents.boss_agent import BossAgent
from app.agents.worker_agent import WorkerAgent
from app.core.event_bus import event_bus
from app.db.repository import save_agent, load_project_agents, load_project_messages, load_project

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self):
        self.boss: Optional[BossAgent] = None
        self.workers: dict[str, WorkerAgent] = {}
        self.current_project_id: Optional[str] = None

    async def create_boss(self, project_id: str, name: str = "Boss") -> BossAgent:
        agent = Agent(
            name=name,
            role=AgentRole.boss,
            project_id=project_id,
            skills=["management", "planning", "coordination", "leadership"],
            personality="experienced engineering manager, decisive and clear communicator",
            provider=settings.llm_default_provider,
            model=settings.llm_default_model,
        )
        self.boss = BossAgent(agent)
        await self.boss.start()
        await event_bus.publish("agent_created", agent.model_dump())
        asyncio.create_task(save_agent(agent))
        asyncio.create_task(self._restore_project(project_id))
        self.current_project_id = project_id
        return self.boss

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
            self.boss.project.id = project_id if self.boss.project else None

    async def _restore_project(self, project_id: str):
        try:
            workers = await load_project_agents(project_id)
            for a in workers:
                if a.role == AgentRole.boss:
                    if self.boss:
                        self.boss.agent.chat_history = a.chat_history
                        self.boss.agent.memory = a.memory
                elif a.id not in self.workers:
                    w = WorkerAgent(a)
                    self.workers[a.id] = w

            msgs = await load_project_messages(project_id)
            if self.boss:
                for m in msgs:
                    if m.msg_type not in ("task_update", "review"):
                        self.boss.agent.chat_history.append(
                            {"role": "user" if m.sender_role == "user" else "assistant", "content": m.content}
                        )
            logger.info("Restored %d workers, %d messages for project %s", len(workers), len(msgs), project_id)
        except Exception as e:
            logger.warning("Project restore skipped: %s", e)

    async def create_worker(self, project_id: str, name: str, role: AgentRole, skills: Optional[list[str]] = None) -> WorkerAgent:
        agent = Agent(
            name=name,
            role=role,
            project_id=project_id,
            skills=skills or [role.value],
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
