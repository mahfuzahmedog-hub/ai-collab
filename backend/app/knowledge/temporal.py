from __future__ import annotations
import logging
import math
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TemporalMemory:
    def __init__(self, decay_rate: float = 0.01, boost_on_access: float = 0.2):
        self._items: dict[str, dict] = {}
        self.decay_rate = decay_rate
        self.boost_on_access = boost_on_access

    def add(self, key: str, content: Any, importance: float = 1.0, metadata: Optional[dict] = None):
        self._items[key] = {
            "key": key, "content": content, "importance": importance,
            "initial_importance": importance,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).timestamp(),
            "last_accessed": datetime.now(timezone.utc).timestamp(),
            "access_count": 0,
        }

    def get(self, key: str) -> Optional[Any]:
        item = self._items.get(key)
        if item:
            item["access_count"] += 1
            item["last_accessed"] = datetime.now(timezone.utc).timestamp()
            item["importance"] = min(item["initial_importance"],
                                     item["importance"] + self.boost_on_access)
        return item["content"] if item else None

    def score(self, key: str, current_time: Optional[float] = None) -> float:
        item = self._items.get(key)
        if not item:
            return 0.0
        t = current_time or datetime.now(timezone.utc).timestamp()
        hours_since_access = (t - item["last_accessed"]) / 3600
        decayed = item["importance"] * math.exp(-self.decay_rate * hours_since_access)
        frequency_boost = math.log1p(item["access_count"]) * 0.1
        return round(decayed + frequency_boost, 4)

    def top_k(self, k: int = 10) -> list[dict]:
        now = datetime.now(timezone.utc).timestamp()
        scored = [(self.score(key, now), key) for key in self._items]
        scored.sort(key=lambda x: -x[0])
        return [self._items[key] for _, key in scored[:k]]

    def decay_all(self, factor: float = 0.95):
        for item in self._items.values():
            item["importance"] *= factor

    def remove(self, key: str) -> bool:
        return self._items.pop(key, None) is not None

    def clear(self):
        self._items.clear()

    def size(self) -> int:
        return len(self._items)


temporal_memory = TemporalMemory()
