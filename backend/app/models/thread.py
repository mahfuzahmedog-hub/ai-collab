from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Thread(BaseModel):
    id: str
    project_id: str
    channel: str
    parent_message_id: str
    title: str = ""
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
