from __future__ import annotations
import logging
from typing import Any, Optional

from app.memory.blocks import MemoryBlock
from app.memory.memfs import MemFS

logger = logging.getLogger(__name__)

TOKEN_BUDGET_SYSTEM = 2000
TOKEN_BUDGET_WORKING = 3000
TOKEN_BUDGET_ARCHIVAL = 2000
TOKEN_BUDGET_TOTAL = 8000


def _estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


class ContextManager:
    def __init__(self, memfs: MemFS):
        self.memfs = memfs
        self.max_system_tokens = TOKEN_BUDGET_SYSTEM
        self.max_working_tokens = TOKEN_BUDGET_WORKING
        self.max_archival_tokens = TOKEN_BUDGET_ARCHIVAL

    async def compose_prompt(
        self,
        project_id: str,
        base_system: str,
        recent_history: list[dict],
        query: str = "",
    ) -> list[dict]:
        system_blocks = await self.memfs.list_system_blocks(project_id)
        system_content = base_system
        sys_tokens = _estimate_tokens(base_system)
        for block in system_blocks:
            block_text = f"\n[{block.name}]\n{block.content}"
            if sys_tokens + _estimate_tokens(block_text) <= self.max_system_tokens:
                system_content += block_text
                sys_tokens += _estimate_tokens(block_text)

        memory_blocks = await self._get_relevant_working_blocks(project_id, query)
        memory_content = ""
        mem_tokens = 0
        if memory_blocks:
            memory_content = "\n<recalled_memories>\n"
            for b in memory_blocks:
                entry = f"[{b.name}] {b.content[:300]}"
                if mem_tokens + _estimate_tokens(entry) <= self.max_working_tokens:
                    memory_content += entry + "\n"
                    mem_tokens += _estimate_tokens(entry)
            memory_content += "</recalled_memories>"
            if memory_content.strip("</recalled_memories>\n"):
                system_content += memory_content

        history_tokens = 0
        trimmed_history = []
        for msg in reversed(recent_history):
            t = _estimate_tokens(msg.get("content", ""))
            if history_tokens + t <= self.max_archival_tokens:
                trimmed_history.insert(0, msg)
                history_tokens += t
            else:
                break

        messages = [
            {"role": "system", "content": system_content},
            *trimmed_history,
            {"role": "user", "content": query},
        ]
        total = _estimate_tokens(system_content) + history_tokens + _estimate_tokens(query)
        logger.info("Context composed: %d tokens (sys=%d, history=%d, query=%d)",
                     total, sys_tokens, history_tokens, _estimate_tokens(query))
        return messages

    async def _get_relevant_working_blocks(self, project_id: str, query: str) -> list[MemoryBlock]:
        if not query or not query.strip():
            return []
        return await self.memfs.search_blocks(query, project_id, limit=5)
