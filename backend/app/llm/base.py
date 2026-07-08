from abc import ABC, abstractmethod
from typing import Optional


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


class ProviderConfig:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
