import enum
import re
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


def utcnow_str() -> str:
    return datetime.utcnow().isoformat() + "Z"


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (name or "").strip().lower()).strip("-")


class AgentStatus(str, enum.Enum):
    creating = "creating"
    initializing = "initializing"
    idle = "idle"
    assigned = "assigned"
    planning = "planning"
    waiting_for_dependencies = "waiting_for_dependencies"
    researching = "researching"
    thinking = "thinking"
    working = "working"
    collaborating = "collaborating"
    reviewing = "reviewing"
    awaiting_user_approval = "awaiting_user_approval"
    approved = "approved"
    executing = "executing"
    testing = "testing"
    completed = "completed"
    archived = "archived"
    blocked = "blocked"
    paused = "paused"
    retrying = "retrying"
    failed = "failed"
    awaiting_tool = "awaiting_tool"
    delegated = "delegated"
    error = "error"
    retired = "retired"


PRESENCE_MAP = {
    AgentStatus.idle: "😴",
    AgentStatus.thinking: "🧠",
    AgentStatus.awaiting_tool: "🔧",
    AgentStatus.delegated: "📤",
    AgentStatus.working: "💻",
    AgentStatus.error: "❌",
}


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: f"agent-{uuid.uuid4().hex[:8]}")
    name: str
    normalized_name: str = ""
    specialization: str = ""
    role: str
    personality: str = "professional and helpful"
    display_name: str | None = None
    mission: str | None = None
    reporting_structure: str | None = None
    version: str = "1.0"
    is_permanent: bool = False
    channel: str = "general"
    emoji: str = ""
    color: str = ""
    max_tokens: int = 4096
    status: AgentStatus = AgentStatus.idle
    current_task_id: str | None = None
    skills: list[str] = Field(default_factory=list)
    memory: dict = Field(default_factory=lambda: {
        "short_term": [],
        "long_term": {},
        "conversation_history": [],
        "completed_tasks": [],
    })
    project_id: str
    chat_history: list[dict] = Field(default_factory=list)
    created_at: str = Field(default_factory=utcnow_str)
    last_active: str = Field(default_factory=utcnow_str)
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7

    @model_validator(mode="after")
    def _derive_normalized_name(self):
        if not self.normalized_name and self.name:
            self.normalized_name = normalize_name(self.name)
        return self


