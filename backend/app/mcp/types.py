from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class MCPMethod(Enum):
    initialize = "initialize"
    tools_list = "tools/list"
    tools_call = "tools/call"
    resources_list = "resources/list"
    resources_read = "resources/read"
    prompts_list = "prompts/list"
    prompts_get = "prompts/get"
    ping = "ping"


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResource:
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"


@dataclass
class MCPPrompt:
    name: str
    description: str
    arguments: list[dict] = field(default_factory=list)


@dataclass
class JSONRPCRequest:
    jsonrpc: str = "2.0"
    id: Any = None
    method: str = ""
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = {"jsonrpc": self.jsonrpc, "method": self.method, "params": self.params}
        if self.id is not None:
            d["id"] = self.id
        return d


@dataclass
class JSONRPCResponse:
    jsonrpc: str = "2.0"
    id: Any = None
    result: Any = None
    error: Optional[dict] = None

    def to_dict(self) -> dict:
        d = {"jsonrpc": self.jsonrpc, "id": self.id}
        if self.error:
            d["error"] = self.error
        else:
            d["result"] = self.result
        return d
