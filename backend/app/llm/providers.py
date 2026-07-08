import json
import logging
from typing import AsyncGenerator
import httpx
from app.llm.base import LLMProvider, ProviderConfig
from app.core.config import settings

logger = logging.getLogger(__name__)


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

    @property
    def name(self) -> str:
        return "omniroute"

    async def chat(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.config.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model or "auto",
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def chat_stream(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096):
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST", f"{self.config.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model or "auto",
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
