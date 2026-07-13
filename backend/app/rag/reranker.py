from __future__ import annotations
import json
import logging
from typing import Any, Optional

from app.llm import llm_router

logger = logging.getLogger(__name__)


class Reranker:
    def __init__(self, model: str = "cross-encoder"):
        self.model = model

    async def rerank(self, query: str, results: list[dict], top_k: Optional[int] = None) -> list[dict]:
        if not results:
            return results
        try:
            return await self._llm_rerank(query, results, top_k)
        except Exception as e:
            logger.warning("LLM rerank failed, using score-based: %s", e)
            scored = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
            return scored[:top_k] if top_k else scored

    async def _llm_rerank(self, query: str, results: list[dict], top_k: Optional[int] = None) -> list[dict]:
        items = []
        for i, r in enumerate(results):
            content = r.get("content", r.get("id", ""))[:500]
            items.append({"index": i, "content": content})
        prompt = f"""Given the query: "{query}"

Rank these items by relevance (0-10 score):

{json.dumps(items, indent=2)}

Return a JSON list of {{"index": int, "score": float}} sorted by score descending."""
        provider = llm_router.get_provider()
        if not provider:
            raise RuntimeError("No LLM provider")
        response = await provider.chat([
            {"role": "system", "content": "You are a search reranker."},
            {"role": "user", "content": prompt},
        ], temperature=0.1)
        import re
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            rankings = json.loads(match.group())
            scored = [(r["score"], results[r["index"]]) for r in rankings if 0 <= r["index"] < len(results)]
            scored.sort(key=lambda x: -x[0])
            reranked = [r for _, r in scored]
            return reranked[:top_k] if top_k else reranked
        return results


reranker = Reranker()
