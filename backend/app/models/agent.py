import enum
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


def utcnow_str() -> str:
    return datetime.utcnow().isoformat() + "Z"


class AgentStatus(str, enum.Enum):
    idle = "idle"
    thinking = "thinking"
    working = "working"
    waiting = "waiting"
    blocked = "blocked"
    reviewing = "reviewing"
    testing = "testing"
    done = "done"


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: f"agent-{uuid.uuid4().hex[:8]}")
    name: str
    role: str
    personality: str = "professional and helpful"
    display_name: str | None = None
    mission: str | None = None
    reporting_structure: str | None = None
    version: str = "1.0"
    is_permanent: bool = False
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


