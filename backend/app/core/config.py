from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Collaboration Platform"
    debug: bool = False
    secret_key: str = "change-me-in-production"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_collab"
    redis_url: str = "redis://localhost:6379/0"

    llm_default_provider: str = "openai"
    llm_default_model: str = "gpt-4o-mini"

    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "gryphe/mythomax-l2-13b"
    omniroute_api_key: Optional[str] = None
    omniroute_base_url: str = "http://localhost:20128/v1"
    omniroute_default_model: str = "auto"
    ollama_base_url: str = "http://localhost:11434"

    max_agents_per_project: int = 50
    task_timeout_minutes: int = 30
    heartbeat_interval: int = 5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
