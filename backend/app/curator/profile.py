from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


class UserProfile:
    def __init__(self, user_id: str, project_id: str):
        self.user_id = user_id
        self.project_id = project_id
        self.preferences: dict[str, Any] = {}
        self.communication_style: str = "professional"
        self.domain_expertise: list[str] = []
        self.frequent_topics: list[str] = []
        self.interaction_count: int = 0
        self.last_updated: str = _utcnow()
        self._dirty: bool = False

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "project_id": self.project_id,
            "preferences": self.preferences,
            "communication_style": self.communication_style,
            "domain_expertise": self.domain_expertise,
            "frequent_topics": self.frequent_topics,
            "interaction_count": self.interaction_count,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        p = cls(data["user_id"], data["project_id"])
        p.preferences = data.get("preferences", {})
        p.communication_style = data.get("communication_style", "professional")
        p.domain_expertise = data.get("domain_expertise", [])
        p.frequent_topics = data.get("frequent_topics", [])
        p.interaction_count = data.get("interaction_count", 0)
        p.last_updated = data.get("last_updated", _utcnow())
        return p

    def update_from_conversation(self, user_msg: str):
        self.interaction_count += 1
        self.last_updated = _utcnow()
        self._dirty = True
        msg_lower = user_msg.lower()
        if any(w in msg_lower for w in ["prefer", "like", "want", "use", "style"]):
            self.preferences["last_preference"] = user_msg[:200]
        topics = []
        for kw in ["python", "javascript", "typescript", "react", "api", "database", "docker", "deploy"]:
            if kw in msg_lower and kw not in self.frequent_topics:
                topics.append(kw)
        if topics:
            self.domain_expertise.extend(topics)
        if len(user_msg) < 60:
            self.communication_style = "concise"
        elif any(w in msg_lower for w in ["please", "thanks", "could you", "would you"]):
            self.communication_style = "polite"
        elif any(w in msg_lower for w in ["urgent", "asap", "fix now", "immediately"]):
            self.communication_style = "direct"

    def to_prompt_block(self) -> str:
        lines = ["<user_profile>"]
        if self.preferences:
            lines.append(f"Preferences: {json.dumps(self.preferences)}")
        if self.domain_expertise:
            lines.append(f"Expertise: {', '.join(self.domain_expertise)}")
        lines.append(f"Style: {self.communication_style}")
        lines.append("</user_profile>")
        return "\n".join(lines)


_profile_cache: dict[str, UserProfile] = {}


async def get_user_profile(user_id: str, project_id: str) -> UserProfile:
    key = f"{project_id}:{user_id}"
    if key in _profile_cache:
        return _profile_cache[key]
    from app.memory.manager import memory_manager
    try:
        results = await memory_manager.search(f"user_profile_{user_id}", project_id=project_id, type_filter="user_profile", limit=1)
        if results:
            data = json.loads(results[0].get("content", "{}"))
            profile = UserProfile.from_dict(data)
            _profile_cache[key] = profile
            return profile
    except Exception:
        pass
    profile = UserProfile(user_id, project_id)
    _profile_cache[key] = profile
    return profile


async def save_user_profile(profile: UserProfile):
    if not profile._dirty:
        return
    from app.memory.manager import memory_manager
    try:
        await memory_manager.save({
            "type": "user_profile",
            "content": json.dumps(profile.to_dict()),
            "scope": "project",
            "source": "curation",
            "project_id": profile.project_id,
            "tags": ["user_profile", profile.user_id],
            "importance": 0.9,
        })
        profile._dirty = False
    except Exception as e:
        logger.warning("save_user_profile failed: %s", e)
