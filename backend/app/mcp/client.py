from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Optional

from app.mcp.types import JSONRPCRequest

logger = logging.getLogger(__name__)


class MCPClient:
    def __init__(self, url: str):
        self.url = url
        self._session: Optional[Any] = None
        self._request_id = 0
        self._capabilities: dict = {}

    async def connect(self):
        import httpx
        self._session = httpx.AsyncClient(base_url=self.url, timeout=30)
        resp = await self._session.post("/", json=JSONRPCRequest(method="initialize", params={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
        }).to_dict())
        result = resp.json()
        self._capabilities = result.get("result", {}).get("capabilities", {})

    async def _request(self, method: str, params: dict = None) -> dict:
        if not self._session:
            await self.connect()
        self._request_id += 1
        resp = await self._session.post("/", json=JSONRPCRequest(method=method, id=self._request_id, params=params or {}).to_dict())
        return resp.json().get("result", {})

    async def list_tools(self) -> list[dict]:
        return await self._request("tools/list")

    async def call_tool(self, name: str, arguments: dict) -> Any:
        return await self._request("tools/call", {"name": name, "arguments": arguments})

    async def list_resources(self) -> list[dict]:
        return await self._request("resources/list")

    async def read_resource(self, uri: str) -> Any:
        return await self._request("resources/read", {"uri": uri})

    async def list_prompts(self) -> list[dict]:
        return await self._request("prompts/list")

    async def get_prompt(self, name: str, arguments: dict = None) -> Any:
        return await self._request("prompts/get", {"name": name, "arguments": arguments or {}})

    async def close(self):
        if self._session:
            await self._session.aclose()
            self._session = None


mcp_clients: dict[str, MCPClient] = {}
