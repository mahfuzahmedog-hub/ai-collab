from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional


class ToolCallRequest:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.name = name
        self.arguments = arguments


class LLMResponse:
    def __init__(self, content: str = "", tool_calls: list[ToolCallRequest] | None = None):
        self.content = content
        self.tool_calls = tool_calls or []

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

    def to_assistant_message(self) -> dict:
        msg: dict[str, Any] = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": tc.arguments}}
                for tc in self.tool_calls
            ]
        return msg


class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        pass

    @abstractmethod
    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def supports_tools(self) -> bool:
        return False

    async def chat_with_tools(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None) -> LLMResponse:
        content = await self.chat(messages, temperature, max_tokens)
        return LLMResponse(content=content)

    async def chat_stream_with_tools(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None):
        async for chunk in self.chat_stream(messages, temperature, max_tokens):
            yield chunk, []


class ProviderConfig:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
