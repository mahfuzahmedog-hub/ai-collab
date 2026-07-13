from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_SKILL_KEYWORDS = {
    "workflow": {"step", "process", "procedure", "always", "every time", "whenever", "template", "automate"},
    "integration": {"api", "endpoint", "webhook", "integration", "connect", "deploy", "pipeline"},
}


def _estimate_importance(user_msg: str, agent_resp: str) -> float:
    score = 0.5
    if any(w in user_msg.lower() for w in ["remember", "important", "critical", "always", "never", "must", "rule"]):
        score += 0.3
    if any(w in agent_resp.lower() for w in ["remember", "important", "critical", "rule", "fact"]):
        score += 0.2
    if len(user_msg) > 200:
        score += 0.1
    return min(1.0, score)


def _detect_category(user_msg: str) -> Optional[str]:
    msg_lower = user_msg.lower()
    for cat, keywords in _SKILL_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return cat
    return None


def _should_create_skill(user_msg: str, agent_resp: str) -> bool:
    if len(user_msg) < 40 or len(agent_resp) < 80:
        return False
    msg_lower = user_msg.lower()
    for keywords in _SKILL_KEYWORDS.values():
        if any(kw in msg_lower for kw in keywords):
            return True
    return False


def evaluate_exchange(
    user_msg: str,
    agent_resp: str,
) -> dict:
    importance = _estimate_importance(user_msg, agent_resp)
    should_create = _should_create_skill(user_msg, agent_resp)
    category = _detect_category(user_msg)
    return {
        "importance": importance,
        "should_create_skill": should_create,
        "suggested_category": category,
        "memory_tags": _suggest_tags(user_msg, agent_resp),
    }


def _suggest_tags(user_msg: str, agent_resp: str) -> list[str]:
    tags = ["conversation"]
    if any(w in user_msg.lower() for w in ["bug", "error", "fix", "issue"]):
        tags.append("bugfix")
    if any(w in user_msg.lower() for w in ["feature", "add", "implement", "new"]):
        tags.append("feature")
    if any(w in user_msg.lower() for w in ["how", "what", "why", "explain", "difference"]):
        tags.append("question")
    if any(w in agent_resp.lower() for w in ["remember", "fact", "note"]):
        tags.append("fact")
    return tags
