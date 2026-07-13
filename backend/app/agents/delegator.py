from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional

from app.models.agent import Agent, AgentStatus
from app.agents.worker_agent import WorkerAgent
from app.core.event_bus import event_bus
from app.db.repository import save_agent

logger = logging.getLogger(__name__)


async def find_agent_for_task(
    team: dict[str, WorkerAgent],
    task: str,
    skills_needed: Optional[list[str]] = None,
) -> Optional[str]:
    if not team:
        return None
    msg_lower = task.lower()
    candidates = []
    for aid, worker in team.items():
        score = 0
        worker_skills = [s.lower() for s in worker.agent.skills]
        worker_role = str(worker.agent.role).lower()
        if skills_needed:
            for need in skills_needed:
                if need.lower() in worker_skills:
                    score += 3
                if need.lower() in worker_role:
                    score += 2
        else:
            for skill in worker_skills:
                if skill in msg_lower:
                    score += 2
            if worker_role in msg_lower:
                score += 1
        candidates.append((score, aid))
    candidates.sort(key=lambda x: -x[0])
    if candidates and candidates[0][0] > 0:
        return candidates[0][1]
    return None


async def delegate_to_agent(
    team: dict[str, WorkerAgent],
    agent_id: str,
    task: str,
    context: Optional[dict[str, Any]] = None,
) -> str:
    worker = team.get(agent_id)
    if not worker:
        return f"Agent {agent_id} not found in team."
    agent_name = worker.agent.name
    await event_bus.publish("delegation", {
        "from": "delegator",
        "to": agent_name,
        "task": task[:200],
    })
    worker.assign_task({"title": task[:80], "description": task, "context": context or {}})
    asyncio.create_task(worker.work_on_task())
    return f"Delegated to {agent_name}: {task[:200]}"
