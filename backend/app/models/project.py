import enum
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectStatus(str, enum.Enum):
    new = "new"
    planning = "planning"
    in_progress = "in_progress"
    review = "review"
    testing = "testing"
    completed = "completed"
    cancelled = "cancelled"


class Project(BaseModel):
    id: str = Field(default_factory=lambda: f"proj-{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.new
    boss_agent_id: Optional[str] = None
    agent_ids: list[str] = Field(default_factory=list)
    task_ids: list[str] = Field(default_factory=list)
    user_id: str = "default-user"
    requirements: str = ""
    deliverables: list[str] = Field(default_factory=list)
    knowledge_base: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    class Config:
        use_enum_values = True
