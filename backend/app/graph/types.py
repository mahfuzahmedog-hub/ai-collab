from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Callable, Optional


class Interrupt(Exception):
    def __init__(self, value: Any):
        self.value = value
        super().__init__(str(value))


@dataclass
class Command:
    update: dict[str, Any] = field(default_factory=dict)
    goto: Optional[str] = None
    subgraph: Optional[Any] = None


@dataclass
class Send:
    node: str
    arg: Any


State = dict[str, Any]
NodeFunction = Callable[..., AsyncIterator[Optional[Command]]]
RouterFunction = Callable[[State], str]
