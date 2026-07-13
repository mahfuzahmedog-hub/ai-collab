from __future__ import annotations
import logging
import time
from collections import defaultdict
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self):
        self._cost: dict[str, float] = defaultdict(float)
        self._tokens: dict[str, int] = defaultdict(int)
        self._latency: dict[str, list[float]] = defaultdict(list)
        self._calls: dict[str, int] = defaultdict(int)

    def record_llm(self, agent_id: str, model: str, in_tokens: int, out_tokens: int, cost: float, latency_ms: float):
        key = f"{agent_id}:{model}"
        self._cost[key] += cost
        self._tokens[key] += in_tokens + out_tokens
        self._latency[key].append(latency_ms)
        self._calls[key] += 1

    def record_tool(self, agent_id: str, tool_name: str, latency_ms: float):
        key = f"{agent_id}:tool:{tool_name}"
        self._latency[key].append(latency_ms)
        self._calls[key] += 1

    def session_summary(self, agent_id: str) -> dict:
        summary = {}
        for key, calls in self._calls.items():
            if key.startswith(f"{agent_id}:"):
                latencies = self._latency.get(key, [])
                summary[key] = {
                    "calls": calls,
                    "total_cost": round(self._cost.get(key, 0.0), 6),
                    "total_tokens": self._tokens.get(key, 0),
                    "avg_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else 0,
                    "max_latency_ms": round(max(latencies), 2) if latencies else 0,
                }
        return summary

    def global_summary(self) -> dict:
        total_cost = sum(self._cost.values())
        total_tokens = sum(self._tokens.values())
        total_calls = sum(self._calls.values())
        return {
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens,
            "total_calls": total_calls,
        }


metrics_collector = MetricsCollector()
