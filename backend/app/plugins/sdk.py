from __future__ import annotations
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class PluginSDK:
    @staticmethod
    def register_tool(name: str, handler: Callable, description: str = "", parameters: dict = None):
        from app.tools.registry import ToolDefinition, tool_registry
        _S = lambda d: {"type": "string", "description": d}
        _O = lambda p, r=None: {"type": "object", "properties": p, "required": r or list(p.keys())}
        tool_registry.register(ToolDefinition(
            name=name, description=description,
            parameters=_O(parameters or {}),
        ))
        from app.agents.base_agent import _TOOL_HANDLERS
        _TOOL_HANDLERS[name] = lambda: handler

    @staticmethod
    def register_provider(name: str, provider_cls):
        from app.llm.router import llm_router
        llm_router.register(name, provider_cls())

    @staticmethod
    def register_skill(name: str, template: str, trigger_phrases: list = None):
        from app.memory.manager import memory_manager
        asyncio.create_task(memory_manager.save_skill({
            "name": name, "description": name,
            "category": "plugin", "prompt_template": template,
            "trigger_phrases": trigger_phrases or [],
        }))

    @staticmethod
    def on_startup(fn: Callable):
        return fn

    @staticmethod
    def on_shutdown(fn: Callable):
        return fn


plugin_sdk = PluginSDK()
