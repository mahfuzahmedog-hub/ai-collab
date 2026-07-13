from __future__ import annotations
import aiosqlite
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

MEMORY_TYPES = {"fact", "conversation", "decision", "code", "user_preference", "user_profile"}
MEMORY_SCOPES = {"agent", "project", "user", "global"}
MEMORY_SOURCES = {"conversation", "curation", "manual"}

_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "data", "memory.db"
)


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _row_to_dict(row) -> dict:
    d = dict(row)
    if "tags" in d and isinstance(d["tags"], str):
        d["tags"] = json.loads(d["tags"])
    if "metadata" in d and isinstance(d["metadata"], str):
        d["metadata"] = json.loads(d["metadata"])
    if d.get("embedding") and isinstance(d["embedding"], bytes):
        d["embedding"] = json.loads(d["embedding"].decode())
    return d


class MemoryManager:
    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def _ensure_db(self):
        if self._conn is not None:
            return
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA busy_timeout=5000")
        await self._init_schema()
        logger.info("Memory DB ready at %s", self.db_path)

    async def _init_schema(self):
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                scope TEXT NOT NULL DEFAULT 'project',
                source TEXT NOT NULL DEFAULT 'conversation',
                tags TEXT NOT NULL DEFAULT '[]',
                importance REAL NOT NULL DEFAULT 0.5,
                access_count INTEGER NOT NULL DEFAULT 0,
                metadata TEXT NOT NULL DEFAULT '{}',
                project_id TEXT,
                agent_id TEXT,
                embedding BLOB,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);
            CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id);
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance DESC);
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                mem_id UNINDEXED, content, tags,
                tokenize='porter unicode61'
            );
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'knowledge',
                prompt_template TEXT NOT NULL,
                trigger_phrases TEXT NOT NULL DEFAULT '[]',
                parameters TEXT NOT NULL DEFAULT '{}',
                usage_count INTEGER NOT NULL DEFAULT 0,
                success_rate REAL NOT NULL DEFAULT 1.0,
                version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                last_used TEXT NOT NULL,
                changelog TEXT NOT NULL DEFAULT '[]',
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_skills_category ON skills(category);
            CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name);
            CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts USING fts5(
                skill_id UNINDEXED, name, description, prompt_template, trigger_phrases,
                tokenize='porter unicode61'
            );
            CREATE TABLE IF NOT EXISTS skill_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id TEXT NOT NULL,
                success INTEGER NOT NULL DEFAULT 1,
                context TEXT,
                duration_ms INTEGER,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_skill_usage_id ON skill_usage(skill_id);
        """)
        await self._conn.commit()

    async def save(self, memory: dict) -> str:
        await self._ensure_db()
        mem_id = memory.get("id", f"mem-{uuid.uuid4().hex[:12]}")
        now = _utcnow()
        embedding = memory.get("embedding")
        emb_blob = None
        if embedding and isinstance(embedding, list):
            emb_blob = json.dumps(embedding).encode()
        row = {
            "id": mem_id,
            "type": memory.get("type", "fact"),
            "content": memory.get("content", ""),
            "scope": memory.get("scope", "project"),
            "source": memory.get("source", "conversation"),
            "tags": json.dumps(memory.get("tags", [])),
            "importance": memory.get("importance", 0.5),
            "access_count": 0,
            "metadata": json.dumps(memory.get("metadata", {})),
            "project_id": memory.get("project_id"),
            "agent_id": memory.get("agent_id"),
            "embedding": emb_blob,
            "created_at": memory.get("created_at", now),
            "last_accessed": now,
        }
        cols = ", ".join(row.keys())
        ph = ", ".join("?" for _ in row)
        await self._conn.execute(f"INSERT OR REPLACE INTO memories ({cols}) VALUES ({ph})", list(row.values()))
        await self._conn.execute(
            "INSERT OR REPLACE INTO memories_fts (mem_id, content, tags) VALUES (?, ?, ?)",
            (mem_id, memory.get("content", ""), row["tags"]),
        )
        await self._conn.commit()
        return mem_id

    async def get(self, mem_id: str) -> Optional[dict]:
        await self._ensure_db()
        cursor = await self._conn.execute("SELECT * FROM memories WHERE id = ?", (mem_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        await self._conn.execute(
            "UPDATE memories SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
            (_utcnow(), mem_id),
        )
        await self._conn.commit()
        return _row_to_dict(row)

    async def search(self, query: str, project_id: Optional[str] = None, agent_id: Optional[str] = None, type_filter: Optional[str] = None, limit: int = 10) -> list[dict]:
        await self._ensure_db()
        safe = query.replace('"', '""')
        fts_query = f'"{safe}" OR {" ".join(safe.split())}'
        sql = "SELECT m.* FROM memories m INNER JOIN memories_fts f ON m.id = f.mem_id WHERE memories_fts MATCH ?"
        params: list[Any] = [fts_query]
        if project_id:
            sql += " AND m.project_id = ?"
            params.append(project_id)
        if agent_id:
            sql += " AND m.agent_id = ?"
            params.append(agent_id)
        if type_filter:
            sql += " AND m.type = ?"
            params.append(type_filter)
        sql += " ORDER BY m.importance DESC, m.last_accessed DESC LIMIT ?"
        params.append(limit)
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]

    async def recall(self, project_id: str, agent_id: Optional[str] = None, limit: int = 20) -> list[dict]:
        await self._ensure_db()
        sql = "SELECT * FROM memories WHERE project_id = ?"
        params: list[Any] = [project_id]
        if agent_id:
            sql += " AND (agent_id = ? OR agent_id IS NULL)"
            params.append(agent_id)
        sql += " ORDER BY importance DESC, access_count DESC, last_accessed DESC LIMIT ?"
        params.append(limit)
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]

    async def forget(self, mem_id: str) -> bool:
        await self._ensure_db()
        cursor = await self._conn.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
        await self._conn.execute("DELETE FROM memories_fts WHERE mem_id = ?", (mem_id,))
        await self._conn.commit()
        return cursor.rowcount > 0

    async def list_by_project(self, project_id: str, type_filter: Optional[str] = None, limit: int = 50) -> list[dict]:
        await self._ensure_db()
        sql = "SELECT * FROM memories WHERE project_id = ?"
        params: list[Any] = [project_id]
        if type_filter:
            sql += " AND type = ?"
            params.append(type_filter)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [_row_to_dict(r) for r in rows]

    async def consolidate(self, project_id: Optional[str] = None) -> int:
        await self._ensure_db()
        sql = "SELECT id, content, type, tags FROM memories WHERE 1=1"
        params: list[Any] = []
        if project_id:
            sql += " AND project_id = ?"
            params.append(project_id)
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        groups: dict[str, list[dict]] = {}
        for row in rows:
            d = dict(row)
            norm = d["content"].strip().lower()
            groups.setdefault(norm, []).append(d)
        merged = 0
        for norm, dupes in groups.items():
            if len(dupes) < 2:
                continue
            keep = dupes[0]
            for dupe in dupes[1:]:
                await self._conn.execute("DELETE FROM memories_fts WHERE mem_id = ?", (dupe["id"],))
                await self._conn.execute("DELETE FROM memories WHERE id = ?", (dupe["id"],))
                merged += 1
            all_tags = set(json.loads(keep.get("tags", "[]")))
            for dupe in dupes[1:]:
                all_tags.update(json.loads(dupe.get("tags", "[]")))
            await self._conn.execute("UPDATE memories SET tags = ? WHERE id = ?", (json.dumps(list(all_tags)), keep["id"]))
        if merged:
            await self._conn.commit()
            logger.info("Consolidated %d duplicate memories", merged)
        return merged

    async def set_embedding(self, mem_id: str, embedding: list[float]):
        await self._ensure_db()
        blob = json.dumps(embedding).encode()
        await self._conn.execute("UPDATE memories SET embedding = ? WHERE id = ?", (blob, mem_id))
        await self._conn.commit()

    async def get_embedding(self, text: str) -> list[float]:
        from app.llm import llm_router
        provider = llm_router.get_provider("omniroute")
        if provider and hasattr(provider, "_client"):
            try:
                resp = await provider._client.post(
                    f"{provider.config.base_url}/embeddings",
                    headers={"Authorization": f"Bearer {provider._next_key()}", "Content-Type": "application/json"},
                    json={"model": "text-embedding-3-small", "input": text},
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["data"][0]["embedding"]
            except Exception as e:
                logger.warning("Embedding via OmniRoute failed: %s", e)
        return []

    async def save_skill(self, skill: dict) -> str:
        await self._ensure_db()
        skill_id = skill.get("id", f"skl-{uuid.uuid4().hex[:12]}")
        now = _utcnow()
        row = {
            "id": skill_id,
            "name": skill["name"],
            "description": skill.get("description", ""),
            "category": skill.get("category", "knowledge"),
            "prompt_template": skill.get("prompt_template", ""),
            "trigger_phrases": json.dumps(skill.get("trigger_phrases", [])),
            "parameters": json.dumps(skill.get("parameters", {})),
            "usage_count": skill.get("usage_count", 0),
            "success_rate": skill.get("success_rate", 1.0),
            "version": skill.get("version", 1),
            "created_at": skill.get("created_at", now),
            "last_used": now,
            "changelog": json.dumps(skill.get("changelog", [])),
            "metadata": json.dumps(skill.get("metadata", {})),
        }
        cols = ", ".join(row.keys())
        ph = ", ".join("?" for _ in row)
        await self._conn.execute(f"INSERT OR REPLACE INTO skills ({cols}) VALUES ({ph})", list(row.values()))
        await self._conn.execute(
            "INSERT OR REPLACE INTO skills_fts (skill_id, name, description, prompt_template, trigger_phrases) VALUES (?, ?, ?, ?, ?)",
            (skill_id, row["name"], row["description"], row["prompt_template"], row["trigger_phrases"]),
        )
        await self._conn.commit()
        return skill_id

    async def get_skill(self, skill_id: str) -> Optional[dict]:
        await self._ensure_db()
        cursor = await self._conn.execute("SELECT * FROM skills WHERE id = ?", (skill_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        d = dict(row)
        for field in ("trigger_phrases", "parameters", "changelog", "metadata"):
            if isinstance(d.get(field), str):
                d[field] = json.loads(d[field])
        return d

    async def get_skill_by_name(self, name: str) -> Optional[dict]:
        await self._ensure_db()
        cursor = await self._conn.execute("SELECT * FROM skills WHERE name = ?", (name,))
        row = await cursor.fetchone()
        if row is None:
            return None
        d = dict(row)
        for field in ("trigger_phrases", "parameters", "changelog", "metadata"):
            if isinstance(d.get(field), str):
                d[field] = json.loads(d[field])
        return d

    async def search_skills(self, query: str, category: Optional[str] = None, limit: int = 10) -> list[dict]:
        await self._ensure_db()
        safe = query.replace('"', '""')
        fts_query = f'"{safe}" OR {" ".join(safe.split())}'
        sql = "SELECT s.* FROM skills s INNER JOIN skills_fts f ON s.id = f.skill_id WHERE skills_fts MATCH ?"
        params: list[Any] = [fts_query]
        if category:
            sql += " AND s.category = ?"
            params.append(category)
        sql += " ORDER BY s.usage_count DESC, s.success_rate DESC LIMIT ?"
        params.append(limit)
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            for field in ("trigger_phrases", "parameters", "changelog", "metadata"):
                if isinstance(d.get(field), str):
                    d[field] = json.loads(d[field])
            results.append(d)
        return results

    async def list_skills(self, category: Optional[str] = None, limit: int = 50) -> list[dict]:
        await self._ensure_db()
        sql = "SELECT * FROM skills"
        params: list[Any] = []
        if category:
            sql += " WHERE category = ?"
            params.append(category)
        sql += " ORDER BY usage_count DESC, last_used DESC LIMIT ?"
        params.append(limit)
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            for field in ("trigger_phrases", "parameters", "changelog", "metadata"):
                if isinstance(d.get(field), str):
                    d[field] = json.loads(d[field])
            results.append(d)
        return results

    async def delete_skill(self, skill_id: str) -> bool:
        await self._ensure_db()
        cursor = await self._conn.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        await self._conn.execute("DELETE FROM skills_fts WHERE skill_id = ?", (skill_id,))
        await self._conn.commit()
        return cursor.rowcount > 0

    async def log_skill_usage(self, skill_id: str, success: bool = True, context: Optional[str] = None, duration_ms: Optional[int] = None):
        await self._ensure_db()
        now = _utcnow()
        await self._conn.execute(
            "INSERT INTO skill_usage (skill_id, success, context, duration_ms, created_at) VALUES (?, ?, ?, ?, ?)",
            (skill_id, 1 if success else 0, context, duration_ms, now),
        )
        await self._conn.execute(
            "UPDATE skills SET usage_count = usage_count + 1, last_used = ? WHERE id = ?",
            (now, skill_id),
        )
        await self._conn.commit()

    async def prune(self, project_id: Optional[str] = None, importance_threshold: float = 0.2, max_memories: int = 500) -> int:
        await self._ensure_db()
        count_sql = "SELECT COUNT(*) as cnt FROM memories"
        del_sql = "DELETE FROM memories WHERE id IN ("
        fts_sql = "DELETE FROM memories_fts WHERE mem_id IN ("
        params: list[Any] = []
        if project_id:
            count_sql += " WHERE project_id = ?"
            params.append(project_id)
        cursor = await self._conn.execute(count_sql, params)
        row = await cursor.fetchone()
        total = row["cnt"] if row else 0
        if total <= max_memories:
            return 0
        excess = total - max_memories
        sub = "SELECT id FROM memories WHERE importance < ?"
        sub_params: list[Any] = [importance_threshold]
        if project_id:
            sub += " AND project_id = ?"
            sub_params.append(project_id)
        sub += " ORDER BY importance ASC, last_accessed ASC LIMIT ?"
        sub_params.append(excess)
        sub_query = f"({sub})"
        await self._conn.execute(del_sql + sub_query + ")", sub_params)
        await self._conn.execute(fts_sql + sub_query + ")", sub_params)
        await self._conn.commit()
        return excess

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None


memory_manager = MemoryManager()
