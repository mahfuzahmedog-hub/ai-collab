from __future__ import annotations
import logging
from typing import Optional
from app.llm.base import LLMProvider, LLMResponse
from app.llm.providers import OpenAIProvider, GroqProvider, GeminiProvider, AnthropicProvider, OllamaProvider, OpenRouterProvider, OmniRouteProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._register_configured()

    def _register_configured(self):
        if settings.openai_api_key:
            self.register("openai", OpenAIProvider())
        if settings.groq_api_key:
            self.register("groq", GroqProvider())
        if settings.google_api_key:
            self.register("gemini", GeminiProvider())
        if settings.anthropic_api_key:
            self.register("anthropic", AnthropicProvider())
        if settings.openrouter_api_key:
            self.register("openrouter", OpenRouterProvider())
        if settings.omniroute_api_key:
            self.register("omniroute", OmniRouteProvider())
        self.register("ollama", OllamaProvider())

    def register(self, name: str, provider: LLMProvider):
        self._providers[name] = provider
        logger.info("Registered LLM provider: %s", name)

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        name = name or settings.llm_default_provider
        provider = self._providers.get(name)
        if not provider:
            logger.warning("Provider '%s' not found, falling back to first available", name)
            provider = next(iter(self._providers.values()), None)
        return provider

    async def chat(self, messages: list[dict], provider: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        p = self.get_provider(provider)
        return await p.chat(messages, temperature, max_tokens)

    async def chat_stream(self, messages: list[dict], provider: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096):
        p = self.get_provider(provider)
        async for chunk in p.chat_stream(messages, temperature, max_tokens):
            yield chunk

    async def chat_with_tools(self, messages: list[dict], provider: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None) -> LLMResponse:
        p = self.get_provider(provider)
        return await p.chat_with_tools(messages, temperature, max_tokens, tools)

    async def chat_stream_with_tools(self, messages: list[dict], provider: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096, tools: list[dict] | None = None):
        p = self.get_provider(provider)
        async for chunk in p.chat_stream_with_tools(messages, temperature, max_tokens, tools):
            yield chunk

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def is_available(self, provider_name: str) -> bool:
        return provider_name in self._providers
