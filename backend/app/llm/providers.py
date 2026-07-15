import asyncio
import json
import logging
from typing import AsyncGenerator
import httpx
from app.llm.base import LLMProvider, ProviderConfig, LLMResponse, ToolCallRequest
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 10
MAX_RETRIES = 3
BASE_DELAY = 1.0

_zen_sem = asyncio.Semaphore(MAX_CONCURRENT)


class OllamaProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            base_url=settings.ollama_base_url,
            model="llama3.2",
        )

    @property
    def name(self) -> str:
        return "ollama"

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.config.base_url}/api/chat",
                json={"model": self.config.model, "messages": messages, "temperature": temperature},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST", f"{self.config.base_url}/api/chat",
                json={"model": self.config.model, "messages": messages, "temperature": temperature, "stream": True},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.strip():
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue


class ZenProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            api_key=settings.zen_api_key,
            base_url=settings.zen_base_url.rstrip("/"),
            model=settings.zen_default_model,
        )
        self._keys = [k.strip() for k in (settings.zen_api_key or "").split(",") if k.strip()]
        self._key_idx = 0
        self._client = httpx.AsyncClient(timeout=120)

    @property
    def name(self) -> str:
        return "zen"

    @property
    def supports_tools(self) -> bool:
        return True

    def reconfigure(self, api_key: str):
        self._keys = [k.strip() for k in (api_key or "").split(",") if k.strip()]
        self._key_idx = 0
        self.config.api_key = api_key

    def _next_key(self) -> str:
        if not self._keys:
            return self.config.api_key or ""
        key = self._keys[self._key_idx % len(self._keys)]
        self._key_idx += 1
        return key

    async def _request(self, body: dict, stream: bool = False):
        key = self._next_key()
        url = f"{self.config.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        if stream:
            return await self._client.stream("POST", url, headers=headers, json=body, timeout=120)
        resp = await self._client.post(url, headers=headers, json=body, timeout=120)
        resp.raise_for_status()
        return resp

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        async with _zen_sem:
            body = {"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
            resp = await self._request(body)
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        async with _zen_sem:
            body = {"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
            async with await self._request(body, stream=True) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    delta = (data.get("choices") or [{}])[0].get("delta", {}) or {}
                    content = delta.get("content") or delta.get("reasoning_content", "")
                    if content:
                        yield content

    async def chat_with_tools(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None) -> LLMResponse:
        async with _zen_sem:
            body = {"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
            if tools:
                body["tools"] = tools
            resp = await self._request(body)
            data = resp.json()
            msg = data["choices"][0]["message"]
            content = msg.get("content", "") or ""
            tool_calls = [ToolCallRequest(id=tc["id"], name=tc["function"]["name"], arguments=tc["function"]["arguments"]) for tc in msg.get("tool_calls", [])]
            return LLMResponse(content=content, tool_calls=tool_calls)

    async def chat_stream_with_tools(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None):
        async with _zen_sem:
            body = {"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
            if tools:
                body["tools"] = tools
            tool_calls_acc: dict[int, dict] = {}
            async with await self._request(body, stream=True) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
                    choices = data.get("choices")
                    if not choices:
                        continue
                    first = choices[0] or {}
                    delta = first.get("delta", {}) or {}
                    content = delta.get("content") or delta.get("reasoning_content", "")
                    if content:
                        yield content
                    for tc in delta.get("tool_calls", []):
                        idx = tc["index"]
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.get("id"):
                            tool_calls_acc[idx]["id"] = tc["id"]
                        if tc.get("function", {}).get("name"):
                            tool_calls_acc[idx]["name"] = tc["function"]["name"]
                        if tc.get("function", {}).get("arguments"):
                            tool_calls_acc[idx]["arguments"] += tc["function"]["arguments"]
            if tool_calls_acc:
                for _, tc in sorted(tool_calls_acc.items()):
                    yield "", [ToolCallRequest(id=tc["id"], name=tc["name"], arguments=tc["arguments"])]
