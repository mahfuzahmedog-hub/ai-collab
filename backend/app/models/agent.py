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


class AgentRole(str, enum.Enum):
    boss = "boss"
    planner = "planner"
    researcher = "researcher"
    architect = "architect"
    backend = "backend_engineer"
    frontend = "frontend_engineer"
    mobile = "mobile_developer"
    ui_designer = "ui_designer"
    ux_designer = "ux_designer"
    devops = "devops"
    infrastructure = "infrastructure_engineer"
    security = "security_engineer"
    database = "database_engineer"
    api = "api_engineer"
    ai_engineer = "ai_engineer"
    documentation = "documentation_writer"
    qa = "qa_engineer"
    reviewer = "reviewer"
    debugger = "debugger"
    performance = "performance_engineer"
    integration = "integration_engineer"
    deployment = "deployment_engineer"


class Agent(BaseModel):
    id: str = Field(default_factory=lambda: f"agent-{uuid.uuid4().hex[:8]}")
    name: str
    role: AgentRole
    personality: str = "professional and helpful"
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

    class Config:
        use_enum_values = True
