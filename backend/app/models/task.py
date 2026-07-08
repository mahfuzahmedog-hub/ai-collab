import enum
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TaskStatus(str, enum.Enum):
    waiting = "waiting"
    planning = "planning"
    assigned = "assigned"
    working = "working"
    blocked = "blocked"
    review = "review"
    testing = "testing"
    revision = "revision"
    completed = "completed"
    rejected = "rejected"
    cancelled = "cancelled"


class TaskPriority(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    project_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.waiting
    priority: TaskPriority = TaskPriority.medium
    assigned_to: Optional[str] = None
    assigned_by: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    subtasks: list[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    reviews: list[dict] = Field(default_factory=list)
    tests: list[dict] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    estimated_hours: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True
