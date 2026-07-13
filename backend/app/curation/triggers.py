from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_message_count = 0


def on_message() -> None:
    global _message_count
    _message_count += 1


def should_curate(user_msg: str) -> bool:
    # ponytail: naive length heuristic — curate anything with enough signal.
    # Upgrade: semantic relevance scoring against the project memory.
    if not user_msg or not user_msg.strip():
        return False
    return len(user_msg.strip()) >= 8
