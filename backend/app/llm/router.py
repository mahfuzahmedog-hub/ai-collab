from __future__ import annotations
import logging
from typing import Optional
from app.llm.base import LLMProvider, LLMResponse
from app.llm.providers import OllamaProvider, ZenProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._register_configured()

    def _register_configured(self):
        self.register("zen", ZenProvider())
        self.register("ollama", OllamaProvider())

    def register(self, name: str, provider: LLMProvider):
        self._providers[name] = provider
        logger.info("Registered LLM provider: %s", name)

    def update_provider_key(self, provider_name: str, api_key: str):
        provider = self._providers.get(provider_name)
        if provider and hasattr(provider, "reconfigure"):
            provider.reconfigure(api_key)
            logger.info("Updated API key for provider: %s", provider_name)

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
