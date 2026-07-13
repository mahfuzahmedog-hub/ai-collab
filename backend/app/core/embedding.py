import itertools
import math
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

_embedding_cache: dict[str, list[float]] = {}

EMBEDDING_MODEL = "voyage-ai/voyage-3"
EMBEDDING_DIM = 1024

# ponytail: omniroute accepts one key per request, but settings may hold a
# comma-joined multi-key string (used for rotation on rate limits). Pick a
# single key per call, rotating like OmniRouteProvider._next_key().
_omni_keys = [k.strip() for k in (settings.omniroute_api_key or "").split(",") if k.strip()]
_omni_key_iter = itertools.cycle(_omni_keys) if _omni_keys else iter(())


def _omni_key() -> str:
    return next(_omni_key_iter, settings.omniroute_api_key or "")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


async def _get_embedding_via_omniroute(text: str) -> list[float]:
    """Get embedding via Omniroute using Voyage AI models."""
    if not settings.omniroute_api_key:
        raise RuntimeError("Omniroute API key not configured")
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{settings.omniroute_base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {_omni_key()}",
                "Content-Type": "application/json",
            },
            json={"model": EMBEDDING_MODEL, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]


async def get_embedding(text: str) -> list[float]:
    if text in _embedding_cache:
        return _embedding_cache[text]
    emb = await _get_embedding_via_omniroute(text)
    _embedding_cache[text] = emb
    return emb


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    uncached = [t for t in texts if t not in _embedding_cache]
    if uncached:
        if not settings.omniroute_api_key:
            raise RuntimeError("Omniroute API key not configured")
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.omniroute_base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {_omni_key()}",
                    "Content-Type": "application/json",
                },
                json={"model": EMBEDDING_MODEL, "input": uncached},
            )
            resp.raise_for_status()
            data = resp.json()
            for t, d in zip(uncached, data["data"]):
                _embedding_cache[t] = d["embedding"]
    return [_embedding_cache[t] for t in texts]
