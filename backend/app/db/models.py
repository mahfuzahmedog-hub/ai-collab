import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, Float, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    project_id = Column(String, nullable=False)
    personality = Column(String(500), default="professional and helpful")
    status = Column(String(50), default="idle")
    current_task_id = Column(String, nullable=True)
    skills = Column(JSON, default=list)
    provider = Column(String(50), default="openai")
    model = Column(String(100), default="gpt-4o-mini")
    temperature = Column(Float, default=0.7)
    memory = Column(JSON, default=dict)
    chat_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    display_name = Column(String(255), nullable=True)
    mission = Column(String(1000), nullable=True)
    reporting_structure = Column(String(500), nullable=True)
    version = Column(String(50), default="1.0")
    is_permanent = Column(Boolean, default=False)
    channel = Column(String(255), default="general")
    emoji = Column(String(50), default="")
    color = Column(String(50), default="")
    max_tokens = Column(Integer, default=4096)


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
    tags = Column(JSON, default=list)
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


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False)
    sender_id = Column(String, nullable=False)
    sender_name = Column(String(255), nullable=False)
    sender_role = Column(String(50), default="")
    content = Column(Text, nullable=False)
    msg_type = Column(String(50), default="chat")
    channel = Column(String(50), default="general")
    reply_to = Column(String, nullable=True)
    mentions = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    msg_metadata = Column("metadata", JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)


class FileModel(Base):
    __tablename__ = "workspace_files"

    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    path = Column(String, nullable=False)
    content = Column(Text, default="")
    file_type = Column(String, default="file")  # "file" or "directory"
    size = Column(Integer, default=0)
    modified = Column(DateTime, default=datetime.utcnow)


class ChannelModel(Base):
    __tablename__ = "project_channels"
    id = Column(String, primary_key=True)
    project_id = Column(String, primary_key=True)  # composite PK with id
    parent_id = Column(String, nullable=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), default="channel")  # "category" or "channel"
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class ThreadModel(Base):
    __tablename__ = "project_threads"
    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    channel = Column(String(50), nullable=False)
    parent_message_id = Column(String, nullable=False)
    title = Column(String(255), default="")
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class KnowledgeBaseModel(Base):
    __tablename__ = "knowledge_bases"
    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    entries = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExecutionLogModel(Base):
    __tablename__ = "execution_logs"
    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=True)
    agent_name = Column(String(255), default="")
    action = Column(String(100), default="llm_call")
    model = Column(String(100), default="")
    provider = Column(String(50), default="")
    status = Column(String(50), default="completed")  # started, completed, failed
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    input_preview = Column(Text, default="")
    output_preview = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationModel(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    user_id = Column(String, default="user", index=True)
    type = Column(String(50), default="system")  # mention, task, approval, system
    title = Column(String(255), default="")
    body = Column(Text, default="")
    link = Column(String(255), nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ApprovalModel(Base):
    __tablename__ = "approvals"
    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=True)
    agent_name = Column(String(255), default="")
    action = Column(String(100), default="")
    description = Column(Text, default="")
    payload = Column(JSON, default=dict)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class LifecycleAuditModel(Base):
    __tablename__ = "lifecycle_audit"
    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=True, index=True)
    agent_name = Column(String(255), default="")
    from_state = Column(String(50), default="")
    to_state = Column(String(50), default="")
    reason = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class MemoryModel(Base):
    __tablename__ = "memories"
    id = Column(String, primary_key=True, default=gen_id)
    project_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=True, index=True)
    scope = Column(String(50), default="project")  # project, agent, user
    type = Column(String(50), default="fact")  # conversation, decision, fact, code, document
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
