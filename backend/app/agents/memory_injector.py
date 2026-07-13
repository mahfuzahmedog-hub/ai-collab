from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_MAX_MEMORY_TOKENS = 2000


def _estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


async def inject_memories(system_prompt: str, project_id: str, agent_id: Optional[str] = None, query: Optional[str] = None) -> str:
    from app.memory.manager import memory_manager

    recalled = []
    if query:
        recalled = await memory_manager.search(query, project_id=project_id, agent_id=agent_id, limit=10)
    if not recalled:
        recalled = await memory_manager.recall(project_id, agent_id=agent_id, limit=15)

    if not recalled:
        return system_prompt

    lines = []
    budget = _MAX_MEMORY_TOKENS
    for m in recalled:
        type_tag = m.get("type", "fact")
        content = m.get("content", "")
        importance = m.get("importance", 0.5)
        tok = _estimate_tokens(content) + 10
        if tok > budget:
            if importance > 0.7:
                content = content[:_MAX_MEMORY_TOKENS * 2]
                tok = _estimate_tokens(content) + 10
            else:
                continue
        budget -= tok
        tag_str = f" [{', '.join(m.get('tags', []))}]" if m.get("tags") else ""
        lines.append(f"  [{type_tag}]{tag_str} {content[:500]}")
        if budget <= 0:
            break

    if not lines:
        return system_prompt

    memory_section = "\n\nRelevant Memories:\n" + "\n".join(lines)
    return system_prompt + memory_section
