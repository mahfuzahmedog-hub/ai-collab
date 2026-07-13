from __future__ import annotations
import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

_MESSAGE_INTERVAL = 5
_PERIODIC_INTERVAL = 1800
_last_curation_time: float = 0
_message_count: int = 0
_curation_tasks: list[Callable] = []


def register_curation_task(task: Callable):
    _curation_tasks.append(task)


def on_message() -> bool:
    global _message_count
    _message_count += 1
    return _message_count % _MESSAGE_INTERVAL == 0


def on_command() -> bool:
    return True


def on_periodic() -> bool:
    global _last_curation_time
    now = time.time()
    if now - _last_curation_time >= _PERIODIC_INTERVAL:
        _last_curation_time = now
        return True
    return False


def on_task_complete() -> bool:
    global _message_count
    _message_count += 1
    return True


def should_curate(message: Optional[str] = None) -> bool:
    if message and message.strip().lower().startswith("/curate"):
        return True
    if on_periodic():
        return True
    return False


def run_all_tasks():
    for task in _curation_tasks:
        try:
            task()
        except Exception as e:
            logger.warning("Curation task failed: %s", e)
