from __future__ import annotations
import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Optional

from app.graph.engine import GraphEngine, START, END
from app.graph.types import Command

logger = logging.getLogger(__name__)


class SpeakerMode(Enum):
    round_robin = "round_robin"
    freeform = "freeform"
    managed = "managed"


class GroupChat:
    def __init__(
        self,
        agents: list[str],
        mode: SpeakerMode = SpeakerMode.round_robin,
        max_turns: int = 10,
        speaker_fn: Optional[Callable[[dict], str]] = None,
    ):
        self.agents = agents
        self.mode = mode
        self.max_turns = max_turns
        self.speaker_fn = speaker_fn

    def build_graph(self, agent_fns: dict[str, callable]) -> GraphEngine:
        builder = GraphEngine()
        builder.set_entry_point("select_speaker")

        async def select_speaker(state: dict) -> Command:
            turn = state.get("_turn", 0)
            if turn >= self.max_turns:
                return Command(goto=END)

            if self.mode == SpeakerMode.round_robin:
                speaker = self.agents[turn % len(self.agents)]
            elif self.mode == SpeakerMode.freeform and self.speaker_fn:
                speaker = self.speaker_fn(state)
            else:
                speaker = self.agents[0]

            return Command(
                update={"_turn": turn + 1, "_speaker": speaker},
                goto=f"agent_{speaker}",
            )

        builder.add_node("select_speaker", select_speaker)

        for agent_name in self.agents:
            fn = agent_fns.get(agent_name)
            if fn:

                async def agent_wrapper(state: dict, _fn=fn, _name=agent_name) -> Command:
                    msg = state.get("_input", "")
                    result = await _fn(_name, msg, state)
                    messages = state.setdefault("chat_history", [])
                    messages.append({"role": "assistant", "sender": _name, "content": result})
                    return Command(goto="select_speaker")

                builder.add_node(f"agent_{agent_name}", agent_wrapper)
            else:

                async def noop(_name=agent_name) -> Command:
                    return Command(goto="select_speaker")

                builder.add_node(f"agent_{agent_name}", noop)

        return builder
