from __future__ import annotations
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from app.memory.blocks import MemoryBlock
from app.memory.memfs import MemFS
from app.llm import llm_router

logger = logging.getLogger(__name__)


class DreamSubagent:
    def __init__(self, memfs: MemFS):
        self.memfs = memfs
        self._running = False
        self._interval = 300

    async def run_once(self, project_id: str, recent_history: list[dict]):
        if not recent_history:
            return
        conversation_text = "\n".join(
            f"[{m.get('role', 'user')}]: {m.get('content', '')[:500]}"
            for m in recent_history[-20:]
        )
        prompt = f"""Review the following conversation history and identify durable lessons, facts, or insights that should be remembered:

{conversation_text}

Extract 1-3 memory blocks in this JSON format:
[{{"name": "short name", "content": "durable fact or insight", "tags": ["tag1", "tag2"], "system": false}}]

Only extract information that is genuinely useful for future conversations."""
        provider = llm_router.get_provider()
        if not provider:
            return
        try:
            response = await provider.chat([
                {"role": "system", "content": "You are a memory consolidation agent. Extract durable memories from conversations."},
                {"role": "user", "content": prompt},
            ], temperature=0.3)
            blocks_data = self._parse_blocks(response)
            for bd in blocks_data:
                block = MemoryBlock(
                    id=f"dream-{uuid.uuid4().hex[:12]}",
                    name=bd.get("name", f"insight-{uuid.uuid4().hex[:6]}"),
                    content=bd.get("content", ""),
                    system_flag=bd.get("system", False),
                    tags=bd.get("tags", []),
                    metadata={"source": "dream", "dreamed_at": datetime.utcnow().isoformat() + "Z"},
                )
                if block.content:
                    await self.memfs.save_block(block, project_id)
                    logger.info("Dream agent saved block: %s", block.name)
        except Exception as e:
            logger.warning("Dream subagent error: %s", e)

    def _parse_blocks(self, text: str) -> list[dict]:
        import re
        try:
            match = re.search(r'\[.*?\]', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return []

    async def start(self, interval: int = 300):
        self._running = True
        self._interval = interval

    async def stop(self):
        self._running = False


dream_subagent = DreamSubagent(None)
