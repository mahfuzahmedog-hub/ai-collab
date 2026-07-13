from __future__ import annotations
import logging
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=lambda: {"type": "object", "properties": {}, "required": []})

    def to_openai_tool(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    _instance: ToolRegistry | None = None

    def __new__(cls) -> ToolRegistry:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: dict[str, ToolDefinition] = {}
        return cls._instance

    def register(self, definition: ToolDefinition):
        self._tools[definition.name] = definition
        logger.debug("Registered tool schema: %s", definition.name)

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def to_openai_schemas(self) -> list[dict]:
        return [t.to_openai_tool() for t in self._tools.values()]


tool_registry = ToolRegistry()
