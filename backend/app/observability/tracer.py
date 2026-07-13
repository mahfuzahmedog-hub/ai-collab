from __future__ import annotations
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class Span:
    def __init__(self, name: str, trace_id: str = "", parent_id: str = ""):
        self.id = f"span-{uuid.uuid4().hex[:12]}"
        self.trace_id = trace_id or f"trace-{uuid.uuid4().hex[:12]}"
        self.parent_id = parent_id
        self.name = name
        self.start_time = time.perf_counter()
        self.end_time: Optional[float] = None
        self.metadata: dict[str, Any] = {}
        self.children: list[Span] = []

    def finish(self, **kwargs):
        self.end_time = time.perf_counter()
        self.metadata.update(kwargs)

    @property
    def duration_ms(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return (time.perf_counter() - self.start_time) * 1000

    def to_dict(self) -> dict:
        return {
            "id": self.id, "trace_id": self.trace_id, "parent_id": self.parent_id,
            "name": self.name, "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
        }


class GraphTracer:
    def __init__(self):
        self._traces: dict[str, Span] = {}
        self._active: dict[str, Span] = {}

    def start_span(self, name: str, trace_key: str = "default", parent_id: str = "") -> Span:
        span = Span(name, parent_id=parent_id)
        self._active[trace_key] = span
        return span

    def end_span(self, span: Span, trace_key: str = "default", **kwargs):
        span.finish(**kwargs)
        if trace_key in self._traces:
            self._traces[trace_key].children.append(span.to_dict())
        else:
            self._traces[trace_key] = span
        self._active.pop(trace_key, None)

    def get_trace(self, trace_key: str) -> Optional[dict]:
        return self._traces.get(trace_key).to_dict() if trace_key in self._traces else None

    def list_traces(self) -> list[str]:
        return list(self._traces.keys())


graph_tracer = GraphTracer()
