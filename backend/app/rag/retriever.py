from __future__ import annotations
import logging
from typing import Any, Optional

from app.memory.manager import memory_manager
from app.memory.memfs import MemFS
from app.rag.strategies import VectorRetrieval, FullTextRetrieval, HybridRetrieval, RetrievalStrategy

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(self, memfs: Optional[MemFS] = None):
        self.memfs = memfs
        self._strategies: dict[str, RetrievalStrategy] = {}

    def register_strategy(self, name: str, strategy: RetrievalStrategy):
        self._strategies[name] = strategy

    async def retrieve(
        self,
        query: str,
        project_id: str = "",
        strategy: str = "hybrid",
        limit: int = 10,
        score_threshold: float = 0.0,
        rerank: bool = False,
    ) -> list[dict]:
        strat = self._strategies.get(strategy)
        if not strat:
            logger.warning("Strategy '%s' not found, using default", strategy)
            strat = self._strategies.get("hybrid") or self._strategies.get("fulltext")

        if strat:
            results = await strat.retrieve(query, limit)
        else:
            results = await self._default_retrieve(query, project_id, limit)

        if score_threshold > 0:
            results = [r for r in results if r.get("score", 1) >= score_threshold]

        if rerank and results and self._reranker:
            results = await self._reranker.rerank(query, results)

        return results[:limit]

    async def _default_retrieve(self, query: str, project_id: str, limit: int) -> list[dict]:
        memories = await memory_manager.search(query, project_id=project_id or None, limit=limit)
        return [
            {"id": m.get("id", ""), "content": m.get("content", ""), "score": m.get("importance", 0.5), "type": m.get("type", ""), "strategy": "default"}
            for m in memories
        ]

    def set_reranker(self, reranker):
        self._reranker = reranker


retrieval_service = RetrievalService()
