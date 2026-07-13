from __future__ import annotations
import json
import logging
import aiosqlite
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SqliteSaver:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def _ensure_db(self):
        if self._conn is not None:
            return
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._init_schema()

    async def _init_schema(self):
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS graph_checkpoints (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                checkpoint_id TEXT NOT NULL PRIMARY KEY,
                parent_checkpoint_id TEXT,
                state BLOB NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_checkpoints_thread
                ON graph_checkpoints(thread_id, checkpoint_ns, checkpoint_id);
            CREATE TABLE IF NOT EXISTS graph_checkpoint_writes (
                thread_id TEXT NOT NULL,
                checkpoint_ns TEXT NOT NULL DEFAULT '',
                checkpoint_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                value BLOB NOT NULL,
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, channel)
            );
        """)
        await self._conn.commit()

    async def put(self, thread_id: str, state: dict, checkpoint_ns: str = "") -> str:
        await self._ensure_db()
        checkpoint_id = f"chk-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}-{hash(str(thread_id)) & 0xFFFF:04x}"
        now = datetime.utcnow().isoformat() + "Z"
        blob = json.dumps(state, default=str).encode()
        await self._conn.execute(
            "INSERT OR REPLACE INTO graph_checkpoints "
            "(thread_id, checkpoint_ns, checkpoint_id, state, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (thread_id, checkpoint_ns, checkpoint_id, blob, now),
        )
        await self._conn.commit()
        return checkpoint_id

    async def get(self, thread_id: str) -> Optional[dict]:
        await self._ensure_db()
        cursor = await self._conn.execute(
            "SELECT state FROM graph_checkpoints WHERE thread_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (thread_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return json.loads(row["state"].decode())

    async def get_tuple(self, thread_id: str) -> Optional[dict]:
        await self._ensure_db()
        cursor = await self._conn.execute(
            "SELECT * FROM graph_checkpoints WHERE thread_id = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (thread_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "thread_id": row["thread_id"],
            "checkpoint_ns": row["checkpoint_ns"],
            "checkpoint_id": row["checkpoint_id"],
            "parent_checkpoint_id": row["parent_checkpoint_id"],
            "state": json.loads(row["state"].decode()),
            "created_at": row["created_at"],
        }

    async def list(self, thread_id: str, limit: int = 10) -> list[dict]:
        await self._ensure_db()
        cursor = await self._conn.execute(
            "SELECT checkpoint_id, created_at, parent_checkpoint_id "
            "FROM graph_checkpoints WHERE thread_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (thread_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def close(self):
        if self._conn:
            await self._conn.close()
            self._conn = None
