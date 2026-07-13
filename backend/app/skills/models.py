from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _gen_id() -> str:
    return f"skl-{uuid.uuid4().hex[:12]}"


class Skill(BaseModel):
    id: str = Field(default_factory=_gen_id)
    name: str
    description: str
    category: str = "knowledge"
    prompt_template: str = ""
    trigger_phrases: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    usage_count: int = 0
    success_rate: float = 1.0
    version: int = 1
    created_at: str = Field(default_factory=_utcnow)
    last_used: str = Field(default_factory=_utcnow)
    changelog: list[dict] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
