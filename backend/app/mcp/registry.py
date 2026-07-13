from __future__ import annotations
import logging
from typing import Optional

from app.mcp.client import MCPClient

logger = logging.getLogger(__name__)


class MCPRegistry:
    def __init__(self):
        self._servers: dict[str, MCPClient] = {}

    async def connect_server(self, name: str, url: str) -> bool:
        client = MCPClient(url)
        await client.connect()
        self._servers[name] = client
        logger.info("Connected MCP server: %s", name)
        return True

    def get(self, name: str) -> Optional[MCPClient]:
        return self._servers.get(name)

    async def disconnect(self, name: str):
        client = self._servers.pop(name, None)
        if client:
            await client.close()

    def list_servers(self) -> list[str]:
        return list(self._servers.keys())


mcp_registry = MCPRegistry()
