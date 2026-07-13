from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ToolPolicy:
    def __init__(self):
        self._per_channel: dict[str, set[str]] = {}
        self._per_role: dict[str, set[str]] = {}
        self._global_allow: set[str] = set()
        self._global_deny: set[str] = set()

    def allow_channel(self, channel: str, tool: str):
        self._per_channel.setdefault(channel, set()).add(tool)

    def deny_channel(self, channel: str, tool: str):
        self._per_channel.setdefault(channel, set()).discard(tool)

    def allow_role(self, role: str, tool: str):
        self._per_role.setdefault(role, set()).add(tool)

    def deny_role(self, role: str, tool: str):
        self._per_role.setdefault(role, set()).discard(tool)

    def allowed(self, tool: str, channel: str = "", role: str = "") -> bool:
        if tool in self._global_deny:
            return False
        if tool in self._global_allow:
            return True
        if channel and channel in self._per_channel:
            if tool in self._per_channel[channel]:
                return True
        if role and role in self._per_role:
            if tool in self._per_role[role]:
                return True
        return tool not in self._global_deny and not self._global_deny


tool_policy = ToolPolicy()
