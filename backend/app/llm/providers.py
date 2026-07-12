import asyncio
import json
import logging
from typing import AsyncGenerator
import httpx
from app.llm.base import LLMProvider, ProviderConfig
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 10
MAX_RETRIES = 3
BASE_DELAY = 1.0

# ponytail: reliable groq models tried in order when the primary 429s.
# Order matters: smaller/faster models first to avoid 413/429 errors.
# These are same-account keys so key rotation can't beat a model-level limit;
# switching models is what actually gets past a per-model rate cap.
OMNIROUTE_FALLBACK_MODELS = [
    "groq/llama-3.1-8b-instant",          # Fast, high rate limits, small context
    "groq/llama-3.1-8b-instant",          # Duplicate for retry
    "auto/best-free",                      # Auto-select best free
    "groq/meta-llama/llama-4-scout-17b-16e-instruct",  # Larger context fallback
    "groq/openai/gpt-oss-120b",           # Large context fallback
    "auto/best-free",                      # Auto-select best free
]

_omniroute_sem = asyncio.Semaphore(MAX_CONCURRENT)


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or "https://api.openai.com/v1",
            model=settings.llm_default_model or "gpt-4o-mini",
        )

    @property
    def name(self) -> str:
        return "openai"

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        if not self.config.api_key:
            return "[OpenAI not configured - set OPENAI_API_KEY]"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"},
                json={"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        if not self.config.api_key:
            yield "[OpenAI not configured]"
            return
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"},
                json={"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue


class GroqProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
            model="mixtral-8x7b-32768",
        )

    @property
    def name(self) -> str:
        return "groq"

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        if not self.config.api_key:
            return "[Groq not configured - set GROQ_API_KEY]"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"},
                json={"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        if not self.config.api_key:
            yield "[Groq not configured]"
            return
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{self.config.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"},
                json={"model": self.config.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue


class GeminiProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            api_key=settings.google_api_key,
            model="gemini-1.5-flash",
        )

    @property
    def name(self) -> str:
        return "gemini"

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        if not self.config.api_key:
            return "[Gemini not configured - set GOOGLE_API_KEY]"
        gemini_messages = self._convert_messages(messages)
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:generateContent?key={self.config.api_key}",
                json={"contents": gemini_messages, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}},
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
            return ""

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        if not self.config.api_key:
            yield "[Gemini not configured]"
            return
        gemini_messages = self._convert_messages(messages)
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.model}:streamGenerateContent?key={self.config.api_key}",
                json={"contents": gemini_messages, "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}},
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            chunk = json.loads(data)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                text = "".join(p.get("text", "") for p in parts)
                                if text:
                                    yield text
                        except json.JSONDecodeError:
                            continue

    def _convert_messages(self, messages: list[dict]) -> list[dict]:
        contents = []
        for msg in messages:
            role = "user" if msg["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        return contents


class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            api_key=settings.anthropic_api_key,
            model="claude-3-haiku-20240307",
        )

    @property
    def name(self) -> str:
        return "anthropic"

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        if not self.config.api_key:
            return "[Anthropic not configured - set ANTHROPIC_API_KEY]"
        system, cleaned = self._split_system(messages)
        async with httpx.AsyncClient(timeout=60) as client:
            body = {"model": self.config.model, "messages": cleaned, "temperature": temperature, "max_tokens": max_tokens}
            if system:
                body["system"] = system
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.config.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        if not self.config.api_key:
            yield "[Anthropic not configured]"
            return
        system, cleaned = self._split_system(messages)
        async with httpx.AsyncClient(timeout=120) as client:
            body = {"model": self.config.model, "messages": cleaned, "temperature": temperature, "max_tokens": max_tokens, "stream": True}
            if system:
                body["system"] = system
            async with client.stream(
                "POST", "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.config.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                json=body,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            chunk = json.loads(data)
                            if chunk.get("type") == "content_block_delta":
                                delta = chunk.get("delta", {}).get("text", "")
                                if delta:
                                    yield delta
                        except json.JSONDecodeError:
                            continue

    def _split_system(self, messages: list[dict]) -> tuple[str, list[dict]]:
        system = ""
        cleaned = []
        for msg in messages:
            if msg["role"] == "system":
                system += msg["content"] + "\n"
            else:
                cleaned.append(msg)
        return system.strip(), cleaned


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
        # Support multiple comma-separated API keys for rotation on rate limits.
        raw = settings.omniroute_api_key or ""
        self._keys = [k.strip() for k in raw.split(",") if k.strip()]
        self._key_idx = 0
        self._client = httpx.AsyncClient(timeout=120)

    @property
    def name(self) -> str:
        return "omniroute"

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
        # ponytail: rotate across keys on 429; total attempts bounded by
        # max(MAX_RETRIES, num_keys) so every key gets a shot before giving up.
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
            # ponytail: OmniRoute can emit trailing/error chunks without a
            # `choices` array (usage or error frames). Guard against missing or
            # empty choices so a single odd frame can't kill the whole stream.
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
                    # Stream completed normally
                    break
                except Exception as e:
                    if yielded:
                        # Already sent tokens — can't switch models mid-stream
                        raise
                    last_exc = e
                    logger.warning("OmniRoute stream model %s failed (%s), trying next", model, str(e)[:120])
                    continue
            else:
                raise last_exc or RuntimeError("OmniRoute: all models failed for stream")


class OpenRouterProvider(LLMProvider):
    def __init__(self):
        self.config = ProviderConfig(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_default_model,
        )

    @property
    def name(self) -> str:
        return "openrouter"

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        if not self.config.api_key:
            return "[OpenRouter not configured - set OPENROUTER_API_KEY]"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        if not self.config.api_key:
            yield "[OpenRouter not configured]"
            return
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                },
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except json.JSONDecodeError:
                            continue
