import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


def utcnow_str() -> str:
    return datetime.utcnow().isoformat() + "Z"


class Message(BaseModel):
    id: str = Field(default_factory=lambda: f"msg-{uuid.uuid4().hex[:8]}")
    project_id: str
    sender_id: str
    sender_name: str
    sender_role: str = ""
    content: str
    msg_type: str = "chat"  # chat, task_update, review, system, file
    reply_to: Optional[str] = None
    mentions: list[str] = Field(default_factory=list)
    attachments: list[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=utcnow_str)
