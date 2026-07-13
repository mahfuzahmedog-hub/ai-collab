from __future__ import annotations
import asyncio
import logging
from typing import Any

from app.graph.types import Command, Send

logger = logging.getLogger(__name__)


class SuperstepExecutor:
    def __init__(self):
        self._pending: list[asyncio.Task] = []

    async def fan_out(self, sends: list[Send]) -> list[tuple[str, Any]]:
        async def run_send(s: Send) -> tuple[str, Any]:
            try:
                result = await s.arg
                return s.node, result
            except Exception as e:
                logger.error("Fan-out node %s error: %s", s.node, e)
                return s.node, {"error": str(e)}

        tasks = [asyncio.create_task(run_send(s)) for s in sends]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        out = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                out.append((sends[i].node, {"error": str(r)}))
            else:
                out.append(r)
        return out

    async def aggregate(self, results: list[tuple[str, Any]], into: dict[str, Any]) -> dict[str, Any]:
        for node_name, result in results:
            if isinstance(result, dict):
                into[node_name] = result
            else:
                into.setdefault("_fan_out", {})[node_name] = result
        return into
