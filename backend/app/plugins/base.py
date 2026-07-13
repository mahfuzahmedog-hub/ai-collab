from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str = ""
    author: str = ""
    tools: list[dict] = field(default_factory=list)
    providers: list[dict] = field(default_factory=list)
    config_schema: dict = field(default_factory=dict)
    entrypoint: str = ""


class Plugin:
    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self._tool_handlers: dict[str, Callable] = {}
        self._on_startup: Optional[Callable] = None
        self._on_shutdown: Optional[Callable] = None

    def register_tool(self, name: str, handler: Callable):
        self._tool_handlers[name] = handler

    def on_startup(self, fn: Callable):
        self._on_startup = fn

    def on_shutdown(self, fn: Callable):
        self._on_shutdown = fn

    async def startup(self):
        if self._on_startup:
            await self._on_startup() if asyncio.iscoroutinefunction(self._on_startup) else self._on_startup()

    async def shutdown(self):
        if self._on_shutdown:
            await self._on_shutdown() if asyncio.iscoroutinefunction(self._on_shutdown) else self._on_shutdown()


def parse_manifest(path: str) -> PluginManifest:
    with open(path) as f:
        data = json.load(f)
    return PluginManifest(
        name=data.get("name", ""),
        version=data.get("version", "0.1.0"),
        description=data.get("description", ""),
        author=data.get("author", ""),
        tools=data.get("tools", []),
        providers=data.get("providers", []),
        config_schema=data.get("config_schema", {}),
        entrypoint=data.get("entrypoint", ""),
    )
