from .router import LLMRouter
from .base import LLMProvider
from .providers import OllamaProvider, OmniRouteProvider

llm_router = LLMRouter()

__all__ = ["llm_router", "LLMProvider"]
