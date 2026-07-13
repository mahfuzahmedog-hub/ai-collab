from __future__ import annotations
import logging
import uuid
from datetime import datetime
from typing import Optional

from app.sessions.models import Session, DMScope

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(self, project_id: str, channel: str = "general", peer_id: str = "", dm_scope: DMScope = DMScope.main) -> Session:
        now = datetime.utcnow().isoformat() + "Z"
        session = Session(
            id=f"ses-{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            channel=channel,
            peer_id=peer_id,
            dm_scope=dm_scope,
            created_at=now,
            last_active=now,
        )
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Optional[Session]:
        session = self._sessions.get(session_id)
        if session:
            session.last_active = datetime.utcnow().isoformat() + "Z"
        return session

    def find(self, project_id: str, channel: str = "", peer_id: str = "") -> Optional[Session]:
        for s in self._sessions.values():
            if s.project_id == project_id:
                if channel and s.channel != channel:
                    continue
                if peer_id and s.peer_id != peer_id:
                    continue
                s.last_active = datetime.utcnow().isoformat() + "Z"
                return s
        return None

    def reset(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.message_count = 0
            session.last_active = datetime.utcnow().isoformat() + "Z"
            return True
        return False

    def increment_count(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.message_count += 1
            session.last_active = datetime.utcnow().isoformat() + "Z"
            return True
        return False

    def prune(self, max_age_hours: int = 24):
        now = datetime.utcnow().timestamp()
        to_remove = []
        for sid, s in self._sessions.items():
            try:
                age = now - datetime.fromisoformat(s.last_active.replace("Z", "+00:00")).timestamp()
                if age > max_age_hours * 3600:
                    to_remove.append(sid)
            except Exception:
                to_remove.append(sid)
        for sid in to_remove:
            del self._sessions[sid]
        if to_remove:
            logger.info("Pruned %d stale sessions", len(to_remove))

    def list_by_project(self, project_id: str) -> list[Session]:
        return [s for s in self._sessions.values() if s.project_id == project_id]


session_manager = SessionManager()
