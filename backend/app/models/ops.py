import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _gen(prefix: str):
    return lambda: f"{prefix}-{uuid.uuid4().hex[:8]}"


class ExecutionLog(BaseModel):
    id: str = Field(default_factory=_gen("log"))
    project_id: str
    agent_id: Optional[str] = None
    agent_name: str = ""
    action: str = "llm_call"
    model: str = ""
    provider: str = ""
    status: str = "completed"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    input_preview: str = ""
    output_preview: str = ""
    created_at: str = Field(default_factory=_utcnow)


class Notification(BaseModel):
    id: str = Field(default_factory=_gen("ntf"))
    project_id: str
    user_id: str = "user"
    type: str = "system"
    title: str = ""
    body: str = ""
    link: Optional[str] = None
    read: bool = False
    created_at: str = Field(default_factory=_utcnow)


class Approval(BaseModel):
    id: str = Field(default_factory=_gen("apr"))
    project_id: str
    agent_id: Optional[str] = None
    agent_name: str = ""
    action: str = ""
    description: str = ""
    payload: dict = Field(default_factory=dict)
    status: str = "pending"
    created_at: str = Field(default_factory=_utcnow)
    resolved_at: Optional[str] = None


class Memory(BaseModel):
    id: str = Field(default_factory=_gen("mem"))
    project_id: str
    agent_id: Optional[str] = None
    scope: str = "project"
    type: str = "fact"
    content: str
    source: str = "conversation"
    tags: list[str] = Field(default_factory=list)
    importance: float = 0.5
    access_count: int = 0
    metadata: dict = Field(default_factory=dict)
    embedding: Optional[list[float]] = None
    created_at: str = Field(default_factory=_utcnow)
    last_accessed: str = Field(default_factory=_utcnow)
