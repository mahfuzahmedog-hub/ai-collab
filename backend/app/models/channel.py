from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Channel(BaseModel):
    id: str
    project_id: str
    parent_id: Optional[str] = None
    name: str
    type: str = "channel"  # "category" | "channel"
    sort_order: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class ChannelTree(Channel):
    children: list["ChannelTree"] = Field(default_factory=list)
