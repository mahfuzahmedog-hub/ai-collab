import asyncio
import logging
from datetime import datetime
from app.models.agent import Agent, AgentStatus
from app.core.event_bus import event_bus
from app.db.repository import save_agent, save_lifecycle_audit

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    AgentStatus.creating: {AgentStatus.initializing, AgentStatus.error},
    AgentStatus.initializing: {AgentStatus.idle, AgentStatus.error},
    AgentStatus.idle: {AgentStatus.assigned, AgentStatus.planning, AgentStatus.researching, AgentStatus.thinking, AgentStatus.working, AgentStatus.collaborating, AgentStatus.reviewing, AgentStatus.paused, AgentStatus.retired},
    AgentStatus.assigned: {AgentStatus.planning, AgentStatus.working, AgentStatus.waiting_for_dependencies, AgentStatus.blocked, AgentStatus.idle, AgentStatus.error},
    AgentStatus.planning: {AgentStatus.working, AgentStatus.waiting_for_dependencies, AgentStatus.reviewing, AgentStatus.blocked, AgentStatus.idle, AgentStatus.error},
    AgentStatus.waiting_for_dependencies: {AgentStatus.working, AgentStatus.planning, AgentStatus.blocked, AgentStatus.idle, AgentStatus.error},
    AgentStatus.researching: {AgentStatus.working, AgentStatus.thinking, AgentStatus.reviewing, AgentStatus.idle, AgentStatus.error},
    AgentStatus.thinking: {AgentStatus.working, AgentStatus.researching, AgentStatus.idle, AgentStatus.error, AgentStatus.blocked},
    AgentStatus.working: {AgentStatus.reviewing, AgentStatus.testing, AgentStatus.blocked, AgentStatus.idle, AgentStatus.error, AgentStatus.collaborating, AgentStatus.awaiting_user_approval, AgentStatus.completed, AgentStatus.failed},
    AgentStatus.collaborating: {AgentStatus.working, AgentStatus.reviewing, AgentStatus.idle, AgentStatus.error},
    AgentStatus.reviewing: {AgentStatus.approved, AgentStatus.working, AgentStatus.idle, AgentStatus.blocked, AgentStatus.error, AgentStatus.failed},
    AgentStatus.awaiting_user_approval: {AgentStatus.approved, AgentStatus.working, AgentStatus.idle, AgentStatus.blocked, AgentStatus.error},
    AgentStatus.approved: {AgentStatus.executing, AgentStatus.idle, AgentStatus.error},
    AgentStatus.executing: {AgentStatus.testing, AgentStatus.completed, AgentStatus.blocked, AgentStatus.idle, AgentStatus.error, AgentStatus.failed},
    AgentStatus.testing: {AgentStatus.completed, AgentStatus.working, AgentStatus.idle, AgentStatus.blocked, AgentStatus.error, AgentStatus.failed},
    AgentStatus.completed: {AgentStatus.idle, AgentStatus.archived, AgentStatus.reviewing, AgentStatus.error},
    AgentStatus.archived: set(),
    AgentStatus.blocked: {AgentStatus.idle, AgentStatus.waiting_for_dependencies, AgentStatus.retrying, AgentStatus.planning, AgentStatus.working, AgentStatus.error},
    AgentStatus.paused: {AgentStatus.idle, AgentStatus.working, AgentStatus.error},
    AgentStatus.retrying: {AgentStatus.working, AgentStatus.planning, AgentStatus.researching, AgentStatus.idle, AgentStatus.error, AgentStatus.failed},
    AgentStatus.failed: {AgentStatus.retrying, AgentStatus.idle, AgentStatus.error, AgentStatus.retired},
    AgentStatus.error: {AgentStatus.retrying, AgentStatus.idle, AgentStatus.retired},
    AgentStatus.retired: set(),
}

NOTIFY_TRANSITIONS = {
    AgentStatus.blocked, AgentStatus.error, AgentStatus.awaiting_user_approval,
    AgentStatus.completed, AgentStatus.failed, AgentStatus.retired,
}


class LifecycleEngine:
    def __init__(self, agent: Agent):
        self.agent = agent

    async def transition_to(self, new_status: AgentStatus, reason: str = "") -> bool:
        old = self.agent.status
        if old == new_status:
            return False
        allowed = VALID_TRANSITIONS.get(old, set())
        if new_status not in allowed:
            logger.warning("Transition %s -> %s not allowed for agent %s", old.value, new_status.value, self.agent.name)
            return False
        self.agent.status = new_status
        self.agent.last_active = datetime.utcnow().isoformat() + "Z"
        event = {
            "type": "lifecycle_state_changed",
            "agent_id": self.agent.id,
            "agent_name": self.agent.name,
            "from_state": old.value,
            "to_state": new_status.value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        await event_bus.publish("lifecycle_state_changed", event)
        if new_status in NOTIFY_TRANSITIONS:
            from app.db.repository import save_notification
            from app.models.ops import Notification
            n = Notification(
                project_id=self.agent.project_id, type="system",
                title=f"Agent {self.agent.name}: {new_status.value}",
                body=reason or f"State changed from {old.value} to {new_status.value}",
                link=f"agent://{self.agent.id}",
            )
            asyncio.create_task(save_notification(n))
            await event_bus.publish("notification", n.model_dump())
        asyncio.create_task(save_lifecycle_audit({
            "project_id": self.agent.project_id,
            "agent_id": self.agent.id,
            "agent_name": self.agent.name,
            "from_state": old.value,
            "to_state": new_status.value,
            "reason": reason,
        }))
        asyncio.create_task(save_agent(self.agent))
        return True
