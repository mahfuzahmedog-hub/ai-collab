import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AgentModel, MessageModel, TaskModel, ProjectModel, FileModel, ChannelModel,
    ThreadModel, KnowledgeBaseModel, ExecutionLogModel, NotificationModel,
    ApprovalModel, MemoryModel, LifecycleAuditModel,
)
from app.db.session import async_session
from app.models.agent import Agent, AgentStatus
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.message import Message
from app.models.project import Project
from app.models.channel import Channel
from app.models.thread import Thread
from app.models.ops import ExecutionLog, Notification, Approval, Memory

logger = logging.getLogger(__name__)


async def save_agent(agent: Agent):
    async with async_session() as session:
        stmt = select(AgentModel).where(AgentModel.id == agent.id)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.utcnow()
        data = {
            "name": agent.name,
            "role": agent.role,
            "project_id": agent.project_id,
            "personality": agent.personality,
            "display_name": agent.display_name,
            "mission": agent.mission,
            "reporting_structure": agent.reporting_structure,
            "version": agent.version,
            "is_permanent": agent.is_permanent,
            "channel": agent.channel,
            "emoji": agent.emoji,
            "color": agent.color,
            "max_tokens": agent.max_tokens,
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
            role=row.role,
            project_id=row.project_id,
            personality=row.personality,
            display_name=row.display_name,
            mission=row.mission,
            reporting_structure=row.reporting_structure,
            version=row.version or "1.0",
            is_permanent=row.is_permanent or False,
            channel=getattr(row, "channel", None) or "general",
            emoji=getattr(row, "emoji", None) or "",
            color=getattr(row, "color", None) or "",
            max_tokens=getattr(row, "max_tokens", None) or 4096,
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
                role=row.role,
                project_id=row.project_id,
                personality=row.personality,
                display_name=row.display_name,
                mission=row.mission,
                reporting_structure=row.reporting_structure,
                version=row.version or "1.0",
                is_permanent=row.is_permanent or False,
                channel=getattr(row, "channel", None) or "general",
                emoji=getattr(row, "emoji", None) or "",
                color=getattr(row, "color", None) or "",
                max_tokens=getattr(row, "max_tokens", None) or 4096,
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
            thread_id=msg.thread_id,
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
                thread_id=row.thread_id,
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


async def save_file_entry(project_id: str, path: str, content: str, file_type: str = "file"):
    async with async_session() as s:
        stmt = select(FileModel).where(
            FileModel.project_id == project_id,
            FileModel.path == path
        )
        result = await s.execute(stmt)
        existing = result.scalar_one_or_none()
        now = datetime.utcnow()
        if existing:
            existing.content = content
            existing.size = len(content.encode("utf-8"))
            existing.modified = now
        else:
            s.add(FileModel(
                project_id=project_id,
                path=path,
                content=content,
                file_type=file_type,
                size=len(content.encode("utf-8")),
                modified=now,
            ))
        await s.commit()


async def load_file_entries(project_id: str) -> list[dict]:
    async with async_session() as s:
        result = await s.execute(
            select(FileModel).where(FileModel.project_id == project_id)
        )
        rows = result.scalars().all()
        return [
            {
                "name": row.path.split("/")[-1],
                "path": row.path,
                "type": row.file_type,
                "size": row.size,
                "modified": row.modified.timestamp() if row.modified else 0,
            }
            for row in rows
        ]


async def delete_file_entry(project_id: str, path: str):
    async with async_session() as s:
        stmt = select(FileModel).where(
            FileModel.project_id == project_id,
            FileModel.path == path
        )
        result = await s.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            await s.delete(row)
            await s.commit()


async def save_channel(channel: Channel):
    async with async_session() as s:
        stmt = select(ChannelModel).where(
            ChannelModel.id == channel.id,
            ChannelModel.project_id == channel.project_id
        )
        result = await s.execute(stmt)
        existing = result.scalar_one_or_none()
        data = {
            "parent_id": channel.parent_id,
            "name": channel.name,
            "type": channel.type,
            "sort_order": channel.sort_order,
        }
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
        else:
            s.add(ChannelModel(id=channel.id, project_id=channel.project_id, **data))
        await s.commit()


async def load_project_channels(project_id: str) -> list[Channel]:
    async with async_session() as s:
        result = await s.execute(
            select(ChannelModel)
            .where(ChannelModel.project_id == project_id)
            .order_by(ChannelModel.sort_order)
        )
        return [Channel(
            id=row.id, project_id=row.project_id,
            parent_id=row.parent_id, name=row.name,
            type=row.type, sort_order=row.sort_order,
        ) for row in result.scalars().all()]


async def load_project_channels_tree(project_id: str) -> list[dict]:
    channels = await load_project_channels(project_id)
    by_id = {}
    roots = []
    for ch in channels:
        node = ch.model_dump()
        node["children"] = []
        by_id[ch.id] = node
    for ch_id, node in by_id.items():
        if node["parent_id"] and node["parent_id"] in by_id:
            by_id[node["parent_id"]]["children"].append(node)
        else:
            roots.append(node)
    return roots


async def delete_project_channels(project_id: str):
    async with async_session() as s:
        await s.execute(
            delete(ChannelModel).where(ChannelModel.project_id == project_id)
        )
        await s.commit()


async def rename_channel(project_id: str, channel_id: str, name: str) -> bool:
    async with async_session() as s:
        result = await s.execute(
            select(ChannelModel).where(
                ChannelModel.id == channel_id,
                ChannelModel.project_id == project_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        row.name = name
        await s.commit()
        return True


async def move_channel(project_id: str, channel_id: str, parent_id: Optional[str]) -> bool:
    async with async_session() as s:
        result = await s.execute(
            select(ChannelModel).where(
                ChannelModel.id == channel_id,
                ChannelModel.project_id == project_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        row.parent_id = parent_id or None
        await s.commit()
        return True


async def delete_channel(project_id: str, channel_id: str) -> list[str]:
    """Delete a channel and all its descendants. Returns the list of deleted ids."""
    async with async_session() as s:
        result = await s.execute(
            select(ChannelModel).where(ChannelModel.project_id == project_id)
        )
        rows = result.scalars().all()
        children_map: dict[str, list[str]] = {}
        for r in rows:
            children_map.setdefault(r.parent_id, []).append(r.id)
        to_delete: list[str] = []
        stack = [channel_id]
        while stack:
            cid = stack.pop()
            to_delete.append(cid)
            stack.extend(children_map.get(cid, []))
        if to_delete:
            await s.execute(
                delete(ChannelModel).where(
                    ChannelModel.project_id == project_id,
                    ChannelModel.id.in_(to_delete),
                )
            )
            await s.commit()
        return to_delete


async def save_thread(thread: Thread) -> Thread:
    async with async_session() as s:
        s.add(ThreadModel(
            id=thread.id, project_id=thread.project_id,
            channel=thread.channel, parent_message_id=thread.parent_message_id,
            title=thread.title, created_by=thread.created_by,
        ))
        await s.commit()
    return thread


async def load_project_threads(project_id: str) -> list[Thread]:
    async with async_session() as s:
        result = await s.execute(
            select(ThreadModel)
            .where(ThreadModel.project_id == project_id)
            .order_by(ThreadModel.created_at.desc())
        )
        return [Thread(
            id=row.id, project_id=row.project_id,
            channel=row.channel, parent_message_id=row.parent_message_id,
            title=row.title, created_by=row.created_by,
            created_at=row.created_at.isoformat() + "Z" if row.created_at else "",
        ) for row in result.scalars().all()]


async def save_knowledge_base_entry(project_id: str, name: str, key: str, value: str):
    async with async_session() as s:
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.project_id == project_id,
            KnowledgeBaseModel.name == name
        )
        result = await s.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            entries = existing.entries or {}
            entries[key] = value
            existing.entries = entries
        else:
            s.add(KnowledgeBaseModel(
                project_id=project_id, name=name,
                entries={key: value}
            ))
        await s.commit()


async def load_knowledge_base(project_id: str, name: str) -> dict:
    async with async_session() as s:
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.project_id == project_id,
            KnowledgeBaseModel.name == name
        )
        result = await s.execute(stmt)
        row = result.scalar_one_or_none()
        return row.entries if row else {}


# ---------- Message edit / delete ----------

async def update_message_content(project_id: str, message_id: str, content: str) -> bool:
    async with async_session() as s:
        row = (await s.execute(
            select(MessageModel).where(
                MessageModel.id == message_id,
                MessageModel.project_id == project_id,
            )
        )).scalar_one_or_none()
        if not row:
            return False
        row.content = content
        await s.commit()
        return True


async def delete_message(project_id: str, message_id: str) -> bool:
    async with async_session() as s:
        result = await s.execute(
            select(MessageModel).where(
                MessageModel.id == message_id,
                MessageModel.project_id == project_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        await s.delete(row)
        await s.commit()
        return True


# ---------- Execution logs (observability) ----------

async def save_execution_log(log: ExecutionLog):
    async with async_session() as s:
        s.add(ExecutionLogModel(
            id=log.id, project_id=log.project_id, agent_id=log.agent_id,
            agent_name=log.agent_name, action=log.action, model=log.model,
            provider=log.provider, status=log.status,
            input_tokens=log.input_tokens, output_tokens=log.output_tokens,
            total_tokens=log.total_tokens, cost_usd=log.cost_usd,
            latency_ms=log.latency_ms, input_preview=log.input_preview,
            output_preview=log.output_preview,
        ))
        await s.commit()


async def load_execution_logs(project_id: str, limit: int = 200) -> list[ExecutionLog]:
    async with async_session() as s:
        result = await s.execute(
            select(ExecutionLogModel)
            .where(ExecutionLogModel.project_id == project_id)
            .order_by(ExecutionLogModel.created_at.desc())
            .limit(limit)
        )
        out = []
        for r in result.scalars().all():
            out.append(ExecutionLog(
                id=r.id, project_id=r.project_id, agent_id=r.agent_id,
                agent_name=r.agent_name or "", action=r.action or "llm_call",
                model=r.model or "", provider=r.provider or "", status=r.status or "completed",
                input_tokens=r.input_tokens or 0, output_tokens=r.output_tokens or 0,
                total_tokens=r.total_tokens or 0, cost_usd=r.cost_usd or 0.0,
                latency_ms=r.latency_ms or 0, input_preview=r.input_preview or "",
                output_preview=r.output_preview or "",
                created_at=(r.created_at.isoformat() + "Z") if r.created_at else "",
            ))
        return out


# ---------- Notifications ----------

async def save_notification(n: Notification):
    async with async_session() as s:
        s.add(NotificationModel(
            id=n.id, project_id=n.project_id, user_id=n.user_id, type=n.type,
            title=n.title, body=n.body, link=n.link, read=n.read,
        ))
        await s.commit()


async def load_notifications(project_id: str, limit: int = 100) -> list[Notification]:
    async with async_session() as s:
        result = await s.execute(
            select(NotificationModel)
            .where(NotificationModel.project_id == project_id)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
        )
        return [Notification(
            id=r.id, project_id=r.project_id, user_id=r.user_id or "user",
            type=r.type or "system", title=r.title or "", body=r.body or "",
            link=r.link, read=bool(r.read),
            created_at=(r.created_at.isoformat() + "Z") if r.created_at else "",
        ) for r in result.scalars().all()]


async def mark_notification_read(project_id: str, notification_id: str) -> bool:
    async with async_session() as s:
        result = await s.execute(
            select(NotificationModel).where(
                NotificationModel.id == notification_id,
                NotificationModel.project_id == project_id,
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        row.read = True
        await s.commit()
        return True


# ---------- Approvals ----------

async def save_approval(a: Approval):
    async with async_session() as s:
        existing = (await s.execute(
            select(ApprovalModel).where(ApprovalModel.id == a.id)
        )).scalar_one_or_none()
        if existing:
            existing.status = a.status
            existing.resolved_at = datetime.utcnow() if a.status != "pending" else None
        else:
            s.add(ApprovalModel(
                id=a.id, project_id=a.project_id, agent_id=a.agent_id,
                agent_name=a.agent_name, action=a.action, description=a.description,
                payload=a.payload, status=a.status,
            ))
        await s.commit()


async def get_approval(approval_id: str) -> Optional[Approval]:
    async with async_session() as s:
        row = (await s.execute(
            select(ApprovalModel).where(ApprovalModel.id == approval_id)
        )).scalar_one_or_none()
        if not row:
            return None
        return Approval(
            id=row.id, project_id=row.project_id, agent_id=row.agent_id,
            agent_name=row.agent_name or "", action=row.action or "",
            description=row.description or "", payload=row.payload or {},
            status=row.status or "pending",
        )


async def load_approvals(project_id: str, limit: int = 100) -> list[Approval]:
    async with async_session() as s:
        result = await s.execute(
            select(ApprovalModel)
            .where(ApprovalModel.project_id == project_id)
            .order_by(ApprovalModel.created_at.desc())
            .limit(limit)
        )
        return [Approval(
            id=r.id, project_id=r.project_id, agent_id=r.agent_id,
            agent_name=r.agent_name or "", action=r.action or "",
            description=r.description or "", payload=r.payload or {},
            status=r.status or "pending",
            created_at=(r.created_at.isoformat() + "Z") if r.created_at else "",
        ) for r in result.scalars().all()]


# ---------- Lifecycle audit ----------

async def save_lifecycle_audit(entry: dict):
    async with async_session() as s:
        s.add(LifecycleAuditModel(
            project_id=entry.get("project_id", ""),
            agent_id=entry.get("agent_id"),
            agent_name=entry.get("agent_name", ""),
            from_state=entry.get("from_state", ""),
            to_state=entry.get("to_state", ""),
            reason=entry.get("reason", ""),
        ))
        await s.commit()


async def load_lifecycle_audits(project_id: str, limit: int = 200) -> list[dict]:
    async with async_session() as s:
        result = await s.execute(
            select(LifecycleAuditModel)
            .where(LifecycleAuditModel.project_id == project_id)
            .order_by(LifecycleAuditModel.created_at.desc())
            .limit(limit)
        )
        return [
            {
                "id": r.id,
                "project_id": r.project_id,
                "agent_id": r.agent_id,
                "agent_name": r.agent_name or "",
                "from_state": r.from_state or "",
                "to_state": r.to_state or "",
                "reason": r.reason or "",
                "created_at": r.created_at.isoformat() + "Z" if r.created_at else "",
            }
            for r in result.scalars().all()
        ]


# ---------- Memory ----------

async def save_memory(m: Memory):
    embedding_json = None
    try:
        from app.core.embedding import get_embedding
        emb = await get_embedding(m.content)
        embedding_json = json.dumps(emb)
        m.embedding = emb
    except Exception:
        pass
    async with async_session() as s:
        s.add(MemoryModel(
            id=m.id, project_id=m.project_id, agent_id=m.agent_id,
            scope=m.scope, type=m.type, content=m.content, tags=m.tags,
            embedding=embedding_json,
        ))
        await s.commit()


async def load_memories(project_id: str, agent_id: Optional[str] = None, limit: int = 200) -> list[Memory]:
    async with async_session() as s:
        stmt = select(MemoryModel).where(MemoryModel.project_id == project_id)
        if agent_id:
            stmt = stmt.where(MemoryModel.agent_id == agent_id)
        stmt = stmt.order_by(MemoryModel.created_at.desc()).limit(limit)
        result = await s.execute(stmt)
        return [Memory(
            id=r.id, project_id=r.project_id, agent_id=r.agent_id,
            scope=r.scope or "project", type=r.type or "fact",
            content=r.content, tags=r.tags or [],
            embedding=json.loads(r.embedding) if r.embedding else None,
            created_at=(r.created_at.isoformat() + "Z") if r.created_at else "",
        ) for r in result.scalars().all()]


async def search_memories(project_id: str, query: str, limit: int = 10, agent_id: Optional[str] = None) -> list[Memory]:
    memories = await load_memories(project_id, agent_id, limit=500)
    if not memories:
        return []
    try:
        from app.core.embedding import get_embedding, cosine_similarity
        query_emb = await get_embedding(query)
    except Exception:
        query_lower = query.lower()
        return [m for m in memories if query_lower in m.content.lower()][:limit]
    scored = [(cosine_similarity(query_emb, m.embedding), m) for m in memories if m.embedding]
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return [m for _, m in scored[:limit]]
    query_lower = query.lower()
    return [m for m in memories if query_lower in m.content.lower()][:limit]