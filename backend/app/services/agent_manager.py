import logging
from typing import Optional
from app.models.agent import Agent, AgentRole, AgentStatus
from app.agents.boss_agent import BossAgent
from app.agents.worker_agent import WorkerAgent
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)


class AgentManager:
    def __init__(self):
        self.boss: Optional[BossAgent] = None
        self.workers: dict[str, WorkerAgent] = {}

    async def create_boss(self, project_id: str, name: str = "Boss") -> BossAgent:
        agent = Agent(
            name=name,
            role=AgentRole.boss,
            project_id=project_id,
            skills=["management", "planning", "coordination", "leadership"],
            personality="experienced engineering manager, decisive and clear communicator",
        )
        self.boss = BossAgent(agent)
        await self.boss.start()
        await event_bus.publish("agent_created", agent.model_dump())
        return self.boss

    async def create_worker(self, project_id: str, name: str, role: AgentRole, skills: Optional[list[str]] = None) -> WorkerAgent:
        agent = Agent(
            name=name,
            role=role,
            project_id=project_id,
            skills=skills or [role.value],
        )
        worker = WorkerAgent(agent)
        self.workers[agent.id] = worker
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
