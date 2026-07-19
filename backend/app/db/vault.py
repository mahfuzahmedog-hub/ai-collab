import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Optional

import yaml

from app.core.config import settings
from app.models.agent import Agent, AgentStatus, normalize_name
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.message import Message
from app.models.project import Project
from app.models.channel import Channel
from app.models.thread import Thread
from app.models.ops import ExecutionLog, Notification, Approval, Memory

logger = logging.getLogger(__name__)

VAULT = settings.vault_path

_SUBDIRS = {
    "project": "_ai/Workspace/Projects",
    "agent": "_ai/Workspace/Agents",
    "channel": "_ai/Workspace/Channels",
    "task": "_ai/Workspace/Tasks",
    "message": "_ai/History/Messages",
    "thread": "_ai/History/Threads",
    "execution_log": "_ai/System/ExecutionLogs",
    "notification": "_ai/System/Notifications",
    "approval": "_ai/System/Approvals",
    "lifecycle_audit": "_ai/System/Audits",
    "memory": "_ai/System/Memories",
    "file": "_ai/System/Files",
}


def _entity_dir(kind: str) -> str:
    return os.path.join(VAULT, _SUBDIRS[kind])


def _entity_path(kind: str, entity_id: str) -> str:
    return os.path.join(_entity_dir(kind), f"{entity_id}.md")


def _project_file(project_id: str) -> str:
    return _entity_path("project", project_id)


_VAULT_INITED = False


async def _ensure_vault():
    global _VAULT_INITED
    if _VAULT_INITED:
        return
    for subdir in _SUBDIRS.values():
        path = os.path.join(VAULT, subdir)
        os.makedirs(path, exist_ok=True)
    _VAULT_INITED = True


def _to_yaml_value(obj):
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def _model_to_dict(model) -> dict:
    data = {}
    for field, value in model.__dict__.items():
        if field.startswith("_"):
            continue
        data[field] = _to_yaml_value(value)
    return data


async def _write_md(path: str, frontmatter: dict, body: str = ""):
    await _ensure_vault()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    def _sync():
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n")
            # manual YAML dump without PyYAML aliases
            f.write(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False))
            f.write("---\n")
            if body:
                f.write(body)

    await asyncio.to_thread(_sync)


async def _read_md(path: str) -> tuple[dict, str]:
    def _sync():
        if not os.path.exists(path):
            return {}, ""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                data = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                data = {}
            return data, parts[2].lstrip("\n")
        return {}, content

    return await asyncio.to_thread(_sync)


async def _exists(path: str) -> bool:
    def _sync():
        return os.path.exists(path)
    return await asyncio.to_thread(_sync)


async def _list_dir(dir_path: str) -> list[str]:
    def _sync():
        if not os.path.isdir(dir_path):
            return []
        return [f.replace(".md", "") for f in os.listdir(dir_path) if f.endswith(".md")]
    return await asyncio.to_thread(_sync)


async def _remove(path: str):
    def _sync():
        if os.path.exists(path):
            os.remove(path)
    await asyncio.to_thread(_sync)


# ---- helpers ----

def _agent_from_dict(d: dict) -> Agent:
    return Agent(
        id=d.get("id", ""),
        name=d.get("name", ""),
        normalized_name=d.get("normalized_name", ""),
        specialization=d.get("specialization", ""),
        role=d.get("role", ""),
        project_id=d.get("project_id", ""),
        personality=d.get("personality", "professional and helpful"),
        display_name=d.get("display_name"),
        mission=d.get("mission"),
        reporting_structure=d.get("reporting_structure"),
        version=d.get("version", "1.0"),
        is_permanent=d.get("is_permanent", False),
        channel=d.get("channel", "general"),
        emoji=d.get("emoji", ""),
        color=d.get("color", ""),
        max_tokens=d.get("max_tokens", 4096),
        status=AgentStatus(d["status"]) if d.get("status") else AgentStatus.idle,
        current_task_id=d.get("current_task_id"),
        skills=d.get("skills", []),
        provider=d.get("provider", "openai"),
        model=d.get("model", "gpt-4o-mini"),
        temperature=d.get("temperature", 0.7),
        memory=d.get("memory", {}),
        chat_history=d.get("chat_history", []),
    )


def _message_from_dict(d: dict) -> Message:
    return Message(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        sender_id=d.get("sender_id", ""),
        sender_name=d.get("sender_name", ""),
        sender_role=d.get("sender_role", ""),
        content=d.get("content", ""),
        msg_type=d.get("msg_type", "chat"),
        channel=d.get("channel", "general"),
        thread_id=d.get("thread_id"),
        reply_to=d.get("reply_to"),
        mentions=d.get("mentions", []),
        attachments=d.get("attachments", []),
        metadata=d.get("metadata", {}),
        timestamp=d.get("timestamp", ""),
    )


def _task_from_dict(d: dict) -> Task:
    return Task(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        title=d.get("title", ""),
        description=d.get("description", ""),
        status=d.get("status", "waiting"),
        priority=d.get("priority", "medium"),
        assigned_to=d.get("assigned_to"),
        assigned_by=d.get("assigned_by"),
        dependencies=d.get("dependencies", []),
        depends_on=d.get("depends_on", []),
        subtasks=d.get("subtasks", []),
        parent_task_id=d.get("parent_task_id"),
        reviews=d.get("reviews", []),
        tests=d.get("tests", []),
        artifacts=d.get("artifacts", []),
        estimated_hours=d.get("estimated_hours"),
    )


def _project_from_dict(d: dict) -> Project:
    return Project(
        id=d.get("id", ""),
        title=d.get("title", ""),
        description=d.get("description", ""),
        status=d.get("status", "new"),
        boss_agent_id=d.get("boss_agent_id"),
        agent_ids=d.get("agent_ids", []),
        task_ids=d.get("task_ids", []),
        user_id=d.get("user_id", "default-user"),
        requirements=d.get("requirements", ""),
        deliverables=d.get("deliverables", []),
        knowledge_base=d.get("knowledge_base", {}),
        tags=d.get("tags", []),
        created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
    )


def _channel_from_dict(d: dict) -> Channel:
    return Channel(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        parent_id=d.get("parent_id"),
        name=d.get("name", ""),
        type=d.get("type", "channel"),
        sort_order=d.get("sort_order", 0),
    )


def _thread_from_dict(d: dict) -> Thread:
    return Thread(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        channel=d.get("channel", ""),
        parent_message_id=d.get("parent_message_id", ""),
        title=d.get("title", ""),
        created_by=d.get("created_by", ""),
        created_at=d.get("created_at", ""),
    )


def _log_from_dict(d: dict) -> ExecutionLog:
    return ExecutionLog(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        agent_id=d.get("agent_id"),
        agent_name=d.get("agent_name", ""),
        action=d.get("action", "llm_call"),
        model=d.get("model", ""),
        provider=d.get("provider", ""),
        status=d.get("status", "completed"),
        input_tokens=d.get("input_tokens", 0),
        output_tokens=d.get("output_tokens", 0),
        total_tokens=d.get("total_tokens", 0),
        cost_usd=d.get("cost_usd", 0.0),
        latency_ms=d.get("latency_ms", 0),
        input_preview=d.get("input_preview", ""),
        output_preview=d.get("output_preview", ""),
        created_at=d.get("created_at", ""),
    )


def _notif_from_dict(d: dict) -> Notification:
    return Notification(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        user_id=d.get("user_id", "user"),
        type=d.get("type", "system"),
        title=d.get("title", ""),
        body=d.get("body", ""),
        link=d.get("link"),
        read=d.get("read", False),
        created_at=d.get("created_at", ""),
    )


def _approval_from_dict(d: dict) -> Approval:
    return Approval(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        agent_id=d.get("agent_id"),
        agent_name=d.get("agent_name", ""),
        action=d.get("action", ""),
        description=d.get("description", ""),
        payload=d.get("payload", {}),
        status=d.get("status", "pending"),
        created_at=d.get("created_at", ""),
    )


def _memory_from_dict(d: dict) -> Memory:
    return Memory(
        id=d.get("id", ""),
        project_id=d.get("project_id", ""),
        agent_id=d.get("agent_id"),
        scope=d.get("scope", "project"),
        type=d.get("type", "fact"),
        content=d.get("content", ""),
        source=d.get("source", "conversation"),
        tags=d.get("tags", []),
        importance=d.get("importance", 0.5),
        access_count=d.get("access_count", 0),
        metadata=d.get("metadata", {}),
        embedding=d.get("embedding"),
        created_at=d.get("created_at", ""),
        last_accessed=d.get("last_accessed", ""),
    )


# ===========================
# PUBLIC API (mirrors repository.py)
# ===========================

# -- Agent --

async def save_agent(agent: Agent):
    path = _entity_path("agent", agent.id)
    data = _model_to_dict(agent)
    data["status"] = agent.status.value if hasattr(agent.status, "value") else agent.status
    await _write_md(path, data)


async def load_agent(agent_id: str) -> Optional[Agent]:
    path = _entity_path("agent", agent_id)
    data, _ = await _read_md(path)
    if not data.get("id"):
        return None
    return _agent_from_dict(data)


async def load_project_agents(project_id: str) -> list[Agent]:
    agents = []
    for fname in await _list_dir(_entity_dir("agent")):
        data, _ = await _read_md(os.path.join(_entity_dir("agent"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            agents.append(_agent_from_dict(data))
    return agents


async def find_existing_agent(project_id: str, *, normalized_name: str = "", role: str = "", specialization: str = "") -> Optional[Agent]:
    for fname in await _list_dir(_entity_dir("agent")):
        data, _ = await _read_md(os.path.join(_entity_dir("agent"), f"{fname}.md"))
        if data.get("project_id") != project_id:
            continue
        if normalized_name and data.get("normalized_name") == normalized_name:
            return _agent_from_dict(data)
        if role and specialization and data.get("role") == role and data.get("specialization") == specialization:
            return _agent_from_dict(data)
    return None


async def get_or_create_agent(project_id: str, agent: Agent) -> tuple[Agent, bool]:
    existing = await find_existing_agent(project_id, normalized_name=agent.normalized_name, role=agent.role, specialization=agent.specialization)
    if existing:
        return existing, False
    await save_agent(agent)
    return agent, True


async def delete_agent(agent_id: str):
    await _remove(_entity_path("agent", agent_id))


async def merge_agents(survivor_id: str, duplicate_id: str, project_id: str):
    survivor = await load_agent(survivor_id)
    duplicate = await load_agent(duplicate_id)
    if not survivor or not duplicate:
        return
    existing_ids = {m.get("id", "") for m in (survivor.chat_history or [])}
    for m in (duplicate.chat_history or []):
        if m.get("id", "") not in existing_ids:
            survivor.chat_history.append(m)
    sm = survivor.memory or {}
    dm = duplicate.memory or {}
    for key in ("short_term", "long_term", "conversation_history", "completed_tasks"):
        sv = sm.get(key, [] if isinstance(dm.get(key, []), list) else {})
        dv = dm.get(key, [])
        if isinstance(sv, list) and isinstance(dv, list):
            existing = {json.dumps(i) if isinstance(i, dict) else str(i) for i in sv}
            for item in dv:
                key_repr = json.dumps(item) if isinstance(item, dict) else str(item)
                if key_repr not in existing:
                    sv.append(item)
            sm[key] = sv
    survivor.skills = list(set((survivor.skills or []) + (duplicate.skills or [])))
    survivor.memory = sm
    await save_agent(survivor)
    for msg in await load_project_messages(project_id):
        if msg.sender_id == duplicate_id:
            msg.sender_id = survivor_id
            msg.sender_name = survivor.name
            await save_message(msg)
    await delete_agent(duplicate_id)
    logger.info("Merged agent %s into %s (project %s)", duplicate_id, survivor_id, project_id)


# -- Message --

async def save_message(msg: Message):
    path = _entity_path("message", msg.id)
    data = _model_to_dict(msg)
    await _write_md(path, data)
    # Append to channel file for Obsidian readability
    ch_path = _entity_path("channel", f"{msg.project_id}__{msg.channel}")
    ch_data, ch_body = await _read_md(ch_path)
    if ch_data.get("id"):
        line = f"- **{msg.sender_name}** ({msg.timestamp}): {msg.content}\n"
        ch_body += line
        await _write_md(ch_path, ch_data, ch_body)


async def load_project_messages(project_id: str, limit: int = 200) -> list[Message]:
    messages = []
    for fname in await _list_dir(_entity_dir("message")):
        data, _ = await _read_md(os.path.join(_entity_dir("message"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            messages.append(_message_from_dict(data))
    messages.sort(key=lambda m: m.timestamp)
    return messages[-limit:]


async def update_message_content(project_id: str, message_id: str, content: str) -> bool:
    path = _entity_path("message", message_id)
    data, body = await _read_md(path)
    if not data.get("id"):
        return False
    data["content"] = content
    await _write_md(path, data, body)
    return True


async def delete_message(project_id: str, message_id: str) -> bool:
    path = _entity_path("message", message_id)
    if not await _exists(path):
        return False
    await _remove(path)
    return True


# -- Task --

async def save_task(task: Task):
    path = _entity_path("task", task.id)
    data = _model_to_dict(task)
    await _write_md(path, data)


async def load_project_tasks(project_id: str) -> list[Task]:
    tasks = []
    for fname in await _list_dir(_entity_dir("task")):
        data, _ = await _read_md(os.path.join(_entity_dir("task"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            tasks.append(_task_from_dict(data))
    return tasks


async def update_task_fields(project_id: str, task_id: str, **fields) -> Optional[Task]:
    path = _entity_path("task", task_id)
    data, body = await _read_md(path)
    if not data.get("id"):
        return None
    for k, v in fields.items():
        data[k] = _to_yaml_value(v)
    await _write_md(path, data, body)
    return _task_from_dict(data)


# -- Project --

async def save_project(project: Project):
    path = _project_file(project.id)
    data = _model_to_dict(project)
    await _write_md(path, data)


async def load_all_project_ids() -> list[str]:
    ids = []
    for fname in await _list_dir(_entity_dir("project")):
        data, _ = await _read_md(os.path.join(_entity_dir("project"), f"{fname}.md"))
        if data.get("id"):
            ids.append(data["id"])
    return ids


async def load_project(project_id: str) -> Optional[Project]:
    path = _project_file(project_id)
    data, _ = await _read_md(path)
    if not data.get("id"):
        return None
    return _project_from_dict(data)


# -- File entries (stored as vault files) --

async def save_file_entry(project_id: str, path: str, content: str, file_type: str = "file"):
    safe = path.replace("/", "__").replace("\\", "__")
    fpath = _entity_path("file", f"{project_id}__{safe}")
    data = {
        "project_id": project_id,
        "path": path,
        "file_type": file_type,
        "size": len(content.encode("utf-8")),
        "modified": datetime.utcnow().isoformat(),
    }
    await _write_md(fpath, data, content)


async def load_file_entries(project_id: str) -> list[dict]:
    entries = []
    for fname in await _list_dir(_entity_dir("file")):
        data, body = await _read_md(os.path.join(_entity_dir("file"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            entries.append({
                "name": data.get("path", "").split("/")[-1],
                "path": data.get("path", ""),
                "type": data.get("file_type", "file"),
                "size": data.get("size", 0),
                "modified": data.get("modified", 0),
            })
    return entries


async def get_file_content(project_id: str, path_str: str) -> Optional[str]:
    safe = path_str.replace("/", "__").replace("\\", "__")
    fpath = _entity_path("file", f"{project_id}__{safe}")
    data, body = await _read_md(fpath)
    if not data.get("project_id"):
        return None
    return body


async def delete_file_entry(project_id: str, path_str: str):
    safe = path_str.replace("/", "__").replace("\\", "__")
    await _remove(_entity_path("file", f"{project_id}__{safe}"))


# -- Channel --

async def save_channel(channel: Channel):
    path = _entity_path("channel", f"{channel.project_id}__{channel.id}")
    data = _model_to_dict(channel)
    # Load existing body (messages) if file exists
    _, body = await _read_md(path)
    await _write_md(path, data, body)


async def load_project_channels(project_id: str) -> list[Channel]:
    channels = []
    for fname in await _list_dir(_entity_dir("channel")):
        if not fname.startswith(project_id + "__"):
            continue
        data, _ = await _read_md(os.path.join(_entity_dir("channel"), f"{fname}.md"))
        channels.append(_channel_from_dict(data))
    channels.sort(key=lambda c: c.sort_order)
    return channels


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
    dir_path = _entity_dir("channel")
    for fname in await _list_dir(dir_path):
        if fname.startswith(project_id + "__"):
            await _remove(os.path.join(dir_path, f"{fname}.md"))


async def rename_channel(project_id: str, channel_id: str, name: str) -> bool:
    path = _entity_path("channel", f"{project_id}__{channel_id}")
    data, body = await _read_md(path)
    if not data.get("id"):
        return False
    data["name"] = name
    await _write_md(path, data, body)
    return True


async def move_channel(project_id: str, channel_id: str, parent_id: Optional[str]) -> bool:
    path = _entity_path("channel", f"{project_id}__{channel_id}")
    data, body = await _read_md(path)
    if not data.get("id"):
        return False
    data["parent_id"] = parent_id or None
    await _write_md(path, data, body)
    return True


async def delete_channel(project_id: str, channel_id: str) -> list[str]:
    path = _entity_path("channel", f"{project_id}__{channel_id}")
    await _remove(path)
    return [channel_id]


# -- Thread --

async def save_thread(thread: Thread) -> Thread:
    path = _entity_path("thread", thread.id)
    data = _model_to_dict(thread)
    await _write_md(path, data)
    return thread


async def load_project_threads(project_id: str) -> list[Thread]:
    threads = []
    for fname in await _list_dir(_entity_dir("thread")):
        data, _ = await _read_md(os.path.join(_entity_dir("thread"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            threads.append(_thread_from_dict(data))
    return threads


# -- Knowledge base --

async def save_knowledge_base_entry(project_id: str, name: str, key: str, value: str):
    path = _entity_path("memory", f"kb__{project_id}__{name}")
    data, body = await _read_md(path)
    if not data.get("entries"):
        data = {"project_id": project_id, "name": name, "entries": {}}
    data["entries"][key] = value
    await _write_md(path, data)


async def load_knowledge_base(project_id: str, name: str) -> dict:
    path = _entity_path("memory", f"kb__{project_id}__{name}")
    data, _ = await _read_md(path)
    return data.get("entries", {})


# -- Execution logs --

async def save_execution_log(log: ExecutionLog):
    path = _entity_path("execution_log", log.id)
    data = _model_to_dict(log)
    await _write_md(path, data)


async def load_execution_logs(project_id: str, limit: int = 200) -> list[ExecutionLog]:
    logs = []
    for fname in await _list_dir(_entity_dir("execution_log")):
        data, _ = await _read_md(os.path.join(_entity_dir("execution_log"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            logs.append(_log_from_dict(data))
    logs.sort(key=lambda l: l.created_at, reverse=True)
    return logs[:limit]


# -- Notifications --

async def save_notification(n: Notification):
    path = _entity_path("notification", n.id)
    data = _model_to_dict(n)
    await _write_md(path, data)


async def load_notifications(project_id: str, limit: int = 100) -> list[Notification]:
    notifs = []
    for fname in await _list_dir(_entity_dir("notification")):
        data, _ = await _read_md(os.path.join(_entity_dir("notification"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            notifs.append(_notif_from_dict(data))
    notifs.sort(key=lambda n: n.created_at, reverse=True)
    return notifs[:limit]


async def mark_notification_read(project_id: str, notification_id: str) -> bool:
    path = _entity_path("notification", notification_id)
    data, body = await _read_md(path)
    if not data.get("id"):
        return False
    data["read"] = True
    await _write_md(path, data, body)
    return True


# -- Approvals --

async def save_approval(a: Approval):
    path = _entity_path("approval", a.id)
    data = _model_to_dict(a)
    data["status"] = a.status
    await _write_md(path, data)


async def get_approval(approval_id: str) -> Optional[Approval]:
    path = _entity_path("approval", approval_id)
    data, _ = await _read_md(path)
    if not data.get("id"):
        return None
    return _approval_from_dict(data)


async def load_approvals(project_id: str, limit: int = 100) -> list[Approval]:
    approvals = []
    for fname in await _list_dir(_entity_dir("approval")):
        data, _ = await _read_md(os.path.join(_entity_dir("approval"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            approvals.append(_approval_from_dict(data))
    approvals.sort(key=lambda a: a.created_at, reverse=True)
    return approvals[:limit]


# -- Lifecycle audits --

async def save_lifecycle_audit(entry: dict):
    path = _entity_path("lifecycle_audit", entry.get("id", f"audit-{datetime.utcnow().timestamp()}"))
    await _write_md(path, entry)


async def load_lifecycle_audits(project_id: str, limit: int = 200) -> list[dict]:
    audits = []
    for fname in await _list_dir(_entity_dir("lifecycle_audit")):
        data, _ = await _read_md(os.path.join(_entity_dir("lifecycle_audit"), f"{fname}.md"))
        if data.get("project_id") == project_id:
            audits.append(data)
    audits.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    return audits[:limit]


# -- Memory --

async def save_memory(m: Memory):
    embedding_json = None
    try:
        from app.core.embedding import get_embedding
        emb = await get_embedding(m.content)
        embedding_json = json.dumps(emb)
        m.embedding = emb
    except Exception:
        pass
    path = _entity_path("memory", m.id)
    data = _model_to_dict(m)
    if embedding_json:
        data["embedding"] = embedding_json
    await _write_md(path, data)


async def load_memories(project_id: str, agent_id: Optional[str] = None, limit: int = 200) -> list[Memory]:
    memories = []
    for fname in await _list_dir(_entity_dir("memory")):
        if fname.startswith("kb__"):
            continue
        data, _ = await _read_md(os.path.join(_entity_dir("memory"), f"{fname}.md"))
        if data.get("project_id") != project_id:
            continue
        if agent_id and data.get("agent_id") != agent_id:
            continue
        memories.append(_memory_from_dict(data))
    memories.sort(key=lambda m: m.created_at, reverse=True)
    return memories[:limit]


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
