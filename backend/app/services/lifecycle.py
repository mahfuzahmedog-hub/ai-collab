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
    AgentStatus.idle: {AgentStatus.thinking, AgentStatus.delegated, AgentStatus.paused, AgentStatus.retired},
    AgentStatus.thinking: {AgentStatus.awaiting_tool, AgentStatus.idle, AgentStatus.delegated, AgentStatus.error},
    AgentStatus.awaiting_tool: {AgentStatus.thinking, AgentStatus.idle, AgentStatus.error},
    AgentStatus.delegated: {AgentStatus.thinking, AgentStatus.idle, AgentStatus.error},
    AgentStatus.paused: {AgentStatus.idle, AgentStatus.error},
    AgentStatus.error: {AgentStatus.idle, AgentStatus.retired},
    AgentStatus.retired: set(),
}
_NOTIFY_TRANSITIONS = {
    AgentStatus.error, AgentStatus.retired,
}

NOTIFY_TRANSITIONS = {
    AgentStatus.error, AgentStatus.retired,
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
