import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentModel, MessageModel, TaskModel, ProjectModel
from app.db.session import async_session
from app.models.agent import Agent, AgentStatus, AgentRole
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.message import Message
from app.models.project import Project

logger = logging.getLogger(__name__)


async def save_agent(agent: Agent):
    async with async_session() as session:
        stmt = select(AgentModel).where(AgentModel.id == agent.id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.utcnow()
        data = {
            "name": agent.name,
            "role": agent.role.value if hasattr(agent.role, "value") else agent.role,
            "project_id": agent.project_id,
            "personality": agent.personality,
            "status": agent.status.value if hasattr(agent.status, "value") else agent.status,
            "current_task_id": agent.current_task_id,
            "skills": agent.skills,
            "provider": agent.provider,
            "model": agent.model,
            "temperature": agent.temperature,
            "memory": agent.memory,
            "chat_history": agent.chat_history,
            "last_active": now,
        }
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
        else:
            session.add(AgentModel(id=agent.id, created_at=now, **data))
        await session.commit()


async def load_agent(agent_id: str) -> Optional[Agent]:
    async with async_session() as s:
        result = await s.execute(select(AgentModel).where(AgentModel.id == agent_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return Agent(
            id=row.id,
            name=row.name,
            role=AgentRole(row.role),
            project_id=row.project_id,
            personality=row.personality,
            status=AgentStatus(row.status),
            current_task_id=row.current_task_id,
            skills=row.skills or [],
            provider=row.provider,
            model=row.model,
            temperature=row.temperature,
            memory=row.memory or {},
            chat_history=row.chat_history or [],
        )


async def load_project_agents(project_id: str) -> list[Agent]:
    async with async_session() as s:
        result = await s.execute(
            select(AgentModel).where(AgentModel.project_id == project_id)
        )
        agents = []
        for row in result.scalars().all():
            agents.append(Agent(
                id=row.id,
                name=row.name,
                role=AgentRole(row.role),
                project_id=row.project_id,
                personality=row.personality,
                status=AgentStatus(row.status),
                current_task_id=row.current_task_id,
                skills=row.skills or [],
                provider=row.provider,
                model=row.model,
                temperature=row.temperature,
                memory=row.memory or {},
                chat_history=row.chat_history or [],
            ))
        return agents


async def save_message(msg: Message):
    async with async_session() as s:
        s.add(MessageModel(
            id=msg.id,
            project_id=msg.project_id,
            sender_id=msg.sender_id,
            sender_name=msg.sender_name,
            sender_role=msg.sender_role,
            content=msg.content,
            msg_type=msg.msg_type,
            channel=msg.channel,
            reply_to=msg.reply_to,
            mentions=msg.mentions,
            attachments=msg.attachments,
            msg_metadata=msg.metadata,
            timestamp=datetime.utcnow(),
        ))
        await s.commit()


async def load_project_messages(project_id: str, limit: int = 200) -> list[Message]:
    async with async_session() as s:
        result = await s.execute(
            select(MessageModel)
            .where(MessageModel.project_id == project_id)
            .order_by(MessageModel.timestamp.desc())
            .limit(limit)
        )
        messages = []
        for row in reversed(list(result.scalars().all())):
            messages.append(Message(
                id=row.id,
                project_id=row.project_id,
                sender_id=row.sender_id,
                sender_name=row.sender_name,
                sender_role=row.sender_role,
                content=row.content,
                msg_type=row.msg_type,
                channel=row.channel,
                reply_to=row.reply_to,
                mentions=row.mentions or [],
                attachments=row.attachments or [],
                metadata=row.metadata or {},
                timestamp=row.timestamp.isoformat() + "Z" if row.timestamp else "",
            ))
        return messages


async def save_task(task: Task):
    async with async_session() as s:
        data = {
            "project_id": task.project_id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value if hasattr(task.status, "value") else task.status,
            "priority": task.priority.value if hasattr(task.priority, "value") else task.priority,
            "assigned_to": task.assigned_to,
            "assigned_by": task.assigned_by,
            "dependencies": task.dependencies,
            "depends_on": task.depends_on,
            "subtasks": task.subtasks,
            "parent_task_id": task.parent_task_id,
            "reviews": task.reviews,
            "tests": task.tests,
            "artifacts": task.artifacts,
            "estimated_hours": task.estimated_hours,
        }
        stmt = select(TaskModel).where(TaskModel.id == task.id)
        result = await s.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
        else:
            s.add(TaskModel(id=task.id, **data))
        await s.commit()


async def save_project(project: Project):
    async with async_session() as s:
        stmt = select(ProjectModel).where(ProjectModel.id == project.id)
        result = await s.execute(stmt)
        existing = result.scalar_one_or_none()
        data = {
            "title": project.title,
            "description": project.description,
            "status": project.status.value if hasattr(project.status, "value") else project.status,
            "boss_agent_id": project.boss_agent_id,
            "agent_ids": project.agent_ids,
            "task_ids": project.task_ids,
            "user_id": project.user_id,
            "requirements": project.requirements,
            "deliverables": project.deliverables,
            "knowledge_base": project.knowledge_base,
            "updated_at": datetime.utcnow(),
        }
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
        else:
            s.add(ProjectModel(id=project.id, created_at=datetime.utcnow(), **data))
        await s.commit()


async def load_project(project_id: str) -> Optional[Project]:
    async with async_session() as s:
        result = await s.execute(select(ProjectModel).where(ProjectModel.id == project_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return Project(
            id=row.id,
            title=row.title,
            description=row.description,
            status=row.status,
            boss_agent_id=row.boss_agent_id,
            agent_ids=row.agent_ids or [],
            task_ids=row.task_ids or [],
            user_id=row.user_id,
            requirements=row.requirements,
            deliverables=row.deliverables or [],
            knowledge_base=row.knowledge_base or {},
            created_at=row.created_at.isoformat() + "Z" if row.created_at else "",
            updated_at=row.updated_at.isoformat() + "Z" if row.updated_at else "",
        )