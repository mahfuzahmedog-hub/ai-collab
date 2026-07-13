from __future__ import annotations
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RetrievalStrategy(ABC):
    @abstractmethod
    async def retrieve(self, query: str, limit: int = 10) -> list[dict]:
        pass


class VectorRetrieval(RetrievalStrategy):
    def __init__(self, embed_fn, vector_store: dict[str, list[float]]):
        self.embed_fn = embed_fn
        self.vector_store = vector_store

    async def retrieve(self, query: str, limit: int = 10) -> list[dict]:
        query_vec = await self.embed_fn(query)
        if not query_vec:
            return []
        scored = []
        for doc_id, doc_vec in self.vector_store.items():
            score = self._cosine_sim(query_vec, doc_vec)
            scored.append((score, doc_id))
        scored.sort(key=lambda x: -x[0])
        return [{"id": doc_id, "score": s, "strategy": "vector"} for s, doc_id in scored[:limit]]

    def _cosine_sim(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(x * x for x in b) ** 0.5
        return dot / (na * nb) if na and nb else 0.0


class FullTextRetrieval(RetrievalStrategy):
    def __init__(self, search_fn):
        self.search_fn = search_fn

    async def retrieve(self, query: str, limit: int = 10) -> list[dict]:
        results = await self.search_fn(query, limit=limit)
        return [{**r, "strategy": "fulltext"} for r in results]


class HybridRetrieval(RetrievalStrategy):
    def __init__(self, vector: VectorRetrieval, fulltext: FullTextRetrieval, vector_weight: float = 0.5):
        self.vector = vector
        self.fulltext = fulltext
        self.vector_weight = vector_weight

    async def retrieve(self, query: str, limit: int = 10) -> list[dict]:
        vec_results = await self.vector.retrieve(query, limit * 2)
        ft_results = await self.fulltext.retrieve(query, limit * 2)
        merged = {}
        for r in vec_results:
            merged[r["id"]] = {"id": r["id"], "score": r["score"] * self.vector_weight, "strategy": "hybrid"}
        for r in ft_results:
            if r["id"] in merged:
                merged[r["id"]]["score"] += r.get("score", 0.5) * (1 - self.vector_weight)
            else:
                merged[r["id"]] = {"id": r["id"], "score": r.get("score", 0.5) * (1 - self.vector_weight), "strategy": "hybrid"}
        scored = sorted(merged.values(), key=lambda x: -x["score"])
        return scored[:limit]
