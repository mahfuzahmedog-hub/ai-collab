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

OMNIROUTE_FALLBACK_MODELS = [
    "groq/llama-3.1-8b-instant",
    "groq/llama-3.1-8b-instant",
    "auto/best-free",
    "groq/meta-llama/llama-4-scout-17b-16e-instruct",
    "groq/openai/gpt-oss-120b",
    "auto/best-free",
]

_omniroute_sem = asyncio.Semaphore(MAX_CONCURRENT)


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


class OmniRouteProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            api_key=settings.omniroute_api_key,
            base_url=settings.omniroute_base_url,
            model=settings.omniroute_default_model,
        )
        raw = settings.omniroute_api_key or ""
        self._keys = [k.strip() for k in raw.split(",") if k.strip()]
        self._key_idx = 0
        self._client = httpx.AsyncClient(timeout=120)
        self._last_tool_calls: list[ToolCallRequest] = []

    @property
    def name(self) -> str:
        return "omniroute"

    @property
    def supports_tools(self) -> bool:
        return True

    def _next_key(self) -> str:
        if not self._keys:
            return self.config.api_key or ""
        key = self._keys[self._key_idx % len(self._keys)]
        self._key_idx += 1
        return key

    def _extract_content(self, choice: dict) -> str:
        if not choice:
            return ""
        if "delta" in choice:
            return (
                choice.get("delta", {}).get("content")
                or choice.get("delta", {}).get("reasoning_content", "")
            )
        msg = choice.get("message", choice)
        return (
            msg.get("content")
            or msg.get("reasoning_content", "")
        )

    async def _request(self, body: dict) -> httpx.Response:
        attempts = max(MAX_RETRIES, len(self._keys) or 1)
        last_exc: Exception | None = None
        for attempt in range(attempts):
            key = self._next_key()
            try:
                resp = await self._client.post(
                    f"{self.config.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if resp.status_code in (429, 502, 503) and attempt + 1 < attempts:
                    body_preview = ""
                    try:
                        body_preview = resp.text[:300]
                    except Exception:
                        pass
                    delay = BASE_DELAY * (2 ** min(attempt, 3))
                    logger.warning("OmniRoute %d (attempt %d/%d, key #%d, model=%s): %s | retrying in %.1fs", resp.status_code, attempt + 1, attempts, self._key_idx, body.get("model"), body_preview, delay)
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code >= 400:
                    try:
                        logger.error("OmniRoute %d final (model=%s): %s", resp.status_code, body.get("model"), resp.text[:300])
                    except Exception:
                        pass
                resp.raise_for_status()
                return resp
            except httpx.TimeoutException as e:
                last_exc = e
                if attempt + 1 < attempts:
                    delay = BASE_DELAY * (2 ** min(attempt, 3))
                    logger.warning("OmniRoute timeout (attempt %d/%d), retrying in %.1fs", attempt + 1, attempts, delay)
                    await asyncio.sleep(delay)
                    continue
                raise
        if last_exc:
            raise last_exc
        raise RuntimeError("OmniRoute max retries exceeded")

    def _model_chain(self) -> list[str]:
        primary = self.config.model or "auto/best-free"
        chain = [primary] + [m for m in OMNIROUTE_FALLBACK_MODELS if m != primary]
        return chain

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        async with _omniroute_sem:
            last_exc: Exception | None = None
            for model in self._model_chain():
                try:
                    resp = await self._request({
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": False,
                    })
                    data = resp.json()
                    choices = data.get("choices")
                    if not choices or choices[0] is None:
                        raise RuntimeError(f"OmniRoute returned no choices: {str(data)[:200]}")
                    return self._extract_content(choices[0])
                except Exception as e:
                    last_exc = e
                    logger.warning("OmniRoute model %s failed (%s), trying next", model, str(e)[:120])
                    continue
            if last_exc:
                raise last_exc
            raise RuntimeError("OmniRoute: all models failed")

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        async with _omniroute_sem:
            last_exc: Exception | None = None
            for model in self._model_chain():
                try:
                    key = self._next_key()
                    yielded = False
                    async with self._client.stream(
                        "POST", f"{self.config.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "stream": True,
                        },
                        timeout=120.0,
                    ) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                            except json.JSONDecodeError:
                                continue
                            choices = chunk.get("choices")
                            if not choices:
                                continue
                            first = choices[0] or {}
                            delta = first.get("delta", {}) or {}
                            content = delta.get("content") or delta.get("reasoning_content", "")
                            if content:
                                yielded = True
                                yield content
                    break
                except Exception as e:
                    if yielded:
                        raise
                    last_exc = e
                    logger.warning("OmniRoute stream model %s failed (%s), trying next", model, str(e)[:120])
                    continue
            else:
                raise last_exc or RuntimeError("OmniRoute: all models failed for stream")

    async def chat_with_tools(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None) -> LLMResponse:
        async with _omniroute_sem:
            last_exc: Exception | None = None
            for model in self._model_chain():
                try:
                    body = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
                    if tools:
                        body["tools"] = tools
                    resp = await self._request(body)
                    data = resp.json()
                    choices = data.get("choices")
                    if not choices or choices[0] is None:
                        raise RuntimeError(f"OmniRoute returned no choices: {str(data)[:200]}")
                    msg = choices[0].get("message", choices[0])
                    content = msg.get("content", "") or ""
                    tool_calls = []
                    for tc in msg.get("tool_calls", []):
                        tool_calls.append(ToolCallRequest(id=tc["id"], name=tc["function"]["name"], arguments=tc["function"]["arguments"]))
                    return LLMResponse(content=content, tool_calls=tool_calls)
                except Exception as e:
                    last_exc = e
                    logger.warning("OmniRoute model %s (tools) failed (%s), trying next", model, str(e)[:120])
                    continue
            raise last_exc or RuntimeError("OmniRoute: all models failed for tools")

    async def chat_stream_with_tools(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None):
        async with _omniroute_sem:
            self._last_tool_calls = []
            last_exc: Exception | None = None
            for model in self._model_chain():
                try:
                    key = self._next_key()
                    yielded = False
                    body = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
                    if tools:
                        body["tools"] = tools
                    async with self._client.stream(
                        "POST", f"{self.config.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json=body, timeout=120.0,
                    ) as resp:
                        resp.raise_for_status()
                        tool_calls_acc: dict[int, dict] = {}
                        async for line in resp.aiter_lines():
                            if not line.startswith("data: "):
                                continue
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                            except json.JSONDecodeError:
                                continue
                            choices = chunk.get("choices")
                            if not choices:
                                continue
                            first = choices[0] or {}
                            delta = first.get("delta", {}) or {}
                            content = delta.get("content") or delta.get("reasoning_content", "")
                            if content:
                                yielded = True
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
                            self._last_tool_calls = [
                                ToolCallRequest(id=tc["id"], name=tc["name"], arguments=tc["arguments"])
                                for _, tc in sorted(tool_calls_acc.items())
                            ]
                    break
                except Exception as e:
                    if yielded:
                        raise
                    last_exc = e
                    logger.warning("OmniRoute stream model %s (tools) failed (%s), trying next", model, str(e)[:120])
                    continue
            else:
                raise last_exc or RuntimeError("OmniRoute: all models failed for stream tools")
