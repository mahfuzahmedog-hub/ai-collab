import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="new")
    boss_agent_id = Column(String, nullable=True)
    agent_ids = Column(JSON, default=list)
    task_ids = Column(JSON, default=list)
    user_id = Column(String, default="default-user")
    requirements = Column(Text, default="")
    deliverables = Column(JSON, default=list)
    knowledge_base = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="waiting")
    priority = Column(String(20), default="medium")
    assigned_to = Column(String, nullable=True)
    assigned_by = Column(String, nullable=True)
    dependencies = Column(JSON, default=list)
    depends_on = Column(JSON, default=list)
    subtasks = Column(JSON, default=list)
    parent_task_id = Column(String, nullable=True)
    reviews = Column(JSON, default=list)
    tests = Column(JSON, default=list)
    artifacts = Column(JSON, default=list)
    notes = Column(JSON, default=list)
    estimated_hours = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("ProjectModel", backref="tasks")
