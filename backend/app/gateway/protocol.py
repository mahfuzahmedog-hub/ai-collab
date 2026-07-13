from __future__ import annotations
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class FrameType(Enum):
    connect = "connect"
    request = "request"
    response = "response"
    event = "event"
    ping = "ping"
    pong = "pong"


@dataclass
class GatewayFrame:
    type: FrameType
    id: str = ""
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[dict] = None
    timestamp: float = 0.0

    def to_json(self) -> str:
        d = {"type": self.type.value, "id": self.id or uuid.uuid4().hex[:12], "timestamp": self.timestamp or time.time()}
        if self.method:
            d["method"] = self.method
        if self.params:
            d["params"] = self.params
        if self.result is not None:
            d["result"] = self.result
        if self.error:
            d["error"] = self.error
        return json.dumps(d)

    @classmethod
    def from_json(cls, text: str) -> GatewayFrame:
        d = json.loads(text)
        return cls(
            type=FrameType(d.get("type", "request")),
            id=d.get("id", ""),
            method=d.get("method", ""),
            params=d.get("params", {}),
            result=d.get("result"),
            error=d.get("error"),
            timestamp=d.get("timestamp", 0.0),
        )

    @classmethod
    def request(cls, method: str, params: dict = None) -> GatewayFrame:
        return cls(type=FrameType.request, method=method, params=params or {}, id=uuid.uuid4().hex[:12])

    @classmethod
    def response(cls, request_id: str, result: Any = None, error: Optional[dict] = None) -> GatewayFrame:
        return cls(type=FrameType.response, id=request_id, result=result, error=error)

    @classmethod
    def event(cls, name: str, data: dict = None) -> GatewayFrame:
        return cls(type=FrameType.event, method=name, params=data or {})

    @classmethod
    def ping(cls) -> GatewayFrame:
        return cls(type=FrameType.ping, id=uuid.uuid4().hex[:8])

    @classmethod
    def pong(cls, ping_id: str) -> GatewayFrame:
        return cls(type=FrameType.pong, id=ping_id)
