from __future__ import annotations
import json
import logging
import uuid
from typing import Any, Optional

from app.memory.blocks import MemoryBlock
from app.memory.memfs import MemFS
from app.llm import llm_router

logger = logging.getLogger(__name__)


class ArchivalStorage:
    def __init__(self, memfs: MemFS):
        self.memfs = memfs
        self._embedding_cache: dict[str, list[float]] = {}

    async def store(self, content: str, project_id: str, metadata: Optional[dict] = None) -> str:
        block = MemoryBlock(
            id=f"arch-{uuid.uuid4().hex[:12]}",
            name=metadata.get("name", "archival-record") if metadata else "archival-record",
            content=content,
            tags=metadata.get("tags", ["archival"]) if metadata else ["archival"],
            metadata={
                **(metadata or {}),
                "archived_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            },
        )
        block_id = await self.memfs.save_block(block, project_id + "_archival")
        await self.memfs.archive_block(block_id, project_id + "_archival")
        return block_id

    async def search(self, query: str, project_id: str, limit: int = 10) -> list[MemoryBlock]:
        blocks = await self.memfs.search_blocks(query, project_id + "_archival", limit=limit)
        if blocks:
            return blocks
        return await self._vector_search(query, project_id, limit)

    async def _vector_search(self, query: str, project_id: str, limit: int) -> list[MemoryBlock]:
        embedding = await self._get_embedding(query)
        if not embedding:
            return []
        p = __import__("pathlib").Path(self.memfs.base_path) / "archival" / (project_id + "_archival")
        if not p.exists():
            return []
        scored = []
        for f in p.glob("*.md"):
            text = f.read_text(encoding="utf-8")
            try:
                block = MemoryBlock.from_frontmatter(text)
            except Exception:
                continue
            block_emb = self._embedding_cache.get(block.id)
            if block_emb:
                score = self._cosine_similarity(embedding, block_emb)
                scored.append((score, block))
        scored.sort(key=lambda x: -x[0])
        return [b for _, b in scored[:limit]]

    async def _get_embedding(self, text: str) -> list[float]:
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
                logger.warning("Archival vector search failed: %s", e)
        return []

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        if not na or not nb:
            return 0.0
        return dot / (na * nb)
