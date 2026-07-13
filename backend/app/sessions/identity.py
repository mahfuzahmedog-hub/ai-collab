from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class IdentityLink:
    def __init__(self):
        self._links: dict[str, str] = {}

    def link(self, local_id: str, external_id: str, channel: str = ""):
        key = f"{channel}:{external_id}" if channel else external_id
        self._links[key] = local_id

    def resolve(self, external_id: str, channel: str = "") -> Optional[str]:
        key = f"{channel}:{external_id}" if channel else external_id
        return self._links.get(key)

    def unlink(self, external_id: str, channel: str = ""):
        key = f"{channel}:{external_id}" if channel else external_id
        self._links.pop(key, None)

    def get_linked_identities(self, local_id: str) -> list[dict]:
        result = []
        for key, lid in self._links.items():
            if lid == local_id:
                parts = key.split(":", 1)
                result.append({"channel": parts[0] if len(parts) > 1 else "", "external_id": parts[-1]})
        return result


identity_link = IdentityLink()
