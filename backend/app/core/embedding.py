import math
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

_embedding_cache: dict[str, list[float]] = {}

EMBEDDING_MODEL = "text-embedding-ada-002"


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


async def get_embedding(text: str) -> list[float]:
    if text in _embedding_cache:
        return _embedding_cache[text]
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key not configured")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.openai_base_url or 'https://api.openai.com/v1'}/embeddings",
            headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
            json={"model": EMBEDDING_MODEL, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        emb = data["data"][0]["embedding"]
        _embedding_cache[text] = emb
        return emb


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    uncached = [t for t in texts if t not in _embedding_cache]
    if uncached:
        if not settings.openai_api_key:
            raise RuntimeError("OpenAI API key not configured")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.openai_base_url or 'https://api.openai.com/v1'}/embeddings",
                headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
                json={"model": EMBEDDING_MODEL, "input": uncached},
            )
            resp.raise_for_status()
            data = resp.json()
            for t, d in zip(uncached, data["data"]):
                _embedding_cache[t] = d["embedding"]
    return [_embedding_cache[t] for t in texts]
