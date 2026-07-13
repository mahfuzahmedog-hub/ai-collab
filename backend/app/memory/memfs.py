from __future__ import annotations
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.memory.blocks import MemoryBlock

logger = logging.getLogger(__name__)


class MemFS:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "system").mkdir(exist_ok=True)
        (self.base_path / "blocks").mkdir(exist_ok=True)
        (self.base_path / "archival").mkdir(exist_ok=True)

    def _block_path(self, project_id: str, block_id: str) -> Path:
        p = self.base_path / "blocks" / project_id
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{block_id}.md"

    def _system_path(self, project_id: str, name: str) -> Path:
        p = self.base_path / "system" / project_id
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{name}.md"

    def _archival_path(self, project_id: str, block_id: str) -> Path:
        p = self.base_path / "archival" / project_id
        p.mkdir(parents=True, exist_ok=True)
        return p / f"{block_id}.md"

    async def save_block(self, block: MemoryBlock, project_id: str) -> str:
        block_id = block.id or f"blk-{uuid.uuid4().hex[:12]}"
        block.updated_at = datetime.utcnow().isoformat() + "Z"
        if block.system_flag:
            path = self._system_path(project_id, block.name)
        else:
            path = self._block_path(project_id, block_id)
        content = block.to_frontmatter()
        path.write_text(content, encoding="utf-8")
        return block_id

    async def read_block(self, block_id: str, project_id: str) -> Optional[MemoryBlock]:
        path = self._block_path(project_id, block_id)
        if not path.exists():
            path = self._archival_path(project_id, block_id)
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        return MemoryBlock.from_frontmatter(text)

    async def read_system_block(self, name: str, project_id: str) -> Optional[MemoryBlock]:
        path = self._system_path(project_id, name)
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        return MemoryBlock.from_frontmatter(text)

    async def delete_block(self, block_id: str, project_id: str) -> bool:
        path = self._block_path(project_id, block_id)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_blocks(self, project_id: str) -> list[MemoryBlock]:
        p = self.base_path / "blocks" / project_id
        if not p.exists():
            return []
        blocks = []
        for f in sorted(p.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            try:
                blocks.append(MemoryBlock.from_frontmatter(text))
            except Exception as e:
                logger.warning("Failed to parse block %s: %s", f.name, e)
        return blocks

    async def list_system_blocks(self, project_id: str) -> list[MemoryBlock]:
        p = self.base_path / "system" / project_id
        if not p.exists():
            return []
        blocks = []
        for f in sorted(p.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            try:
                blocks.append(MemoryBlock.from_frontmatter(text))
            except Exception as e:
                logger.warning("Failed to parse system block %s: %s", f.name, e)
        return blocks

    async def archive_block(self, block_id: str, project_id: str) -> bool:
        src = self._block_path(project_id, block_id)
        if not src.exists():
            return False
        dst = self._archival_path(project_id, block_id)
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return True

    async def search_blocks(self, query: str, project_id: str, limit: int = 10) -> list[MemoryBlock]:
        blocks = await self.list_blocks(project_id)
        q = query.lower()
        scored = []
        for b in blocks:
            score = 0
            if q in b.name.lower():
                score += 10
            if q in b.content.lower():
                score += 5
            if any(q in t.lower() for t in b.tags):
                score += 3
            if score > 0:
                scored.append((score, b))
        scored.sort(key=lambda x: -x[0])
        return [b for _, b in scored[:limit]]

    async def get_stats(self, project_id: str) -> dict:
        blocks = await self.list_blocks(project_id)
        system = await self.list_system_blocks(project_id)
        return {
            "total_blocks": len(blocks),
            "system_blocks": len(system),
            "total_chars": sum(len(b) for b in blocks),
            "block_names": [b.name for b in blocks],
        }
