import logging
from typing import Optional
from app.llm.base import LLMProvider
from app.llm.providers import OpenAIProvider, GroqProvider, GeminiProvider, AnthropicProvider, OllamaProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("openai", OpenAIProvider())
        self.register("groq", GroqProvider())
        self.register("gemini", GeminiProvider())
        self.register("anthropic", AnthropicProvider())
        self.register("ollama", OllamaProvider())

    def register(self, name: str, provider: LLMProvider):
        self._providers[name] = provider
        logger.info("Registered LLM provider: %s", name)

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        name = name or settings.llm_default_provider
        provider = self._providers.get(name)
        if not provider:
            logger.warning("Provider '%s' not found, falling back to openai", name)
            provider = self._providers.get("openai", list(self._providers.values())[0])
        return provider

    async def chat(self, messages: list[dict], provider: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        p = self.get_provider(provider)
        return await p.chat(messages, temperature, max_tokens)

    async def chat_stream(self, messages: list[dict], provider: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 4096):
        p = self.get_provider(provider)
        async for chunk in p.chat_stream(messages, temperature, max_tokens):
            yield chunk

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def is_available(self, provider_name: str) -> bool:
        return provider_name in self._providers
