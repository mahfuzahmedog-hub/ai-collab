from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DMScope(Enum):
    main = "main"
    per_peer = "per_peer"
    per_channel_peer = "per_channel_peer"


@dataclass
class Session:
    id: str
    project_id: str
    channel: str = "general"
    peer_id: str = ""
    dm_scope: DMScope = DMScope.main
    message_count: int = 0
    created_at: str = ""
    last_active: str = ""
    metadata: dict = field(default_factory=dict)
