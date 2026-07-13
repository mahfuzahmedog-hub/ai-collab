from __future__ import annotations
import asyncio
import logging
from typing import Any, AsyncIterator, Optional

from app.graph.types import State, Command, Send, NodeFunction, RouterFunction, Interrupt

logger = logging.getLogger(__name__)

START = "__start__"
END = "__end__"


def _default_router(state: State) -> str:
    return END


class GraphEngine:
    def __init__(self, schema: type[dict] | None = None):
        self.schema = schema
        self.nodes: dict[str, NodeFunction] = {START: None}
        self.edges: dict[str, str] = {}
        self.conditional_edges: dict[str, tuple[RouterFunction, dict[str, str]]] = {}
        self.checkpointer = None
        self.interrupt_before: set[str] = set()
        self.interrupt_after: set[str] = set()

    def add_node(self, name: str, fn: NodeFunction):
        self.nodes[name] = fn

    def add_edge(self, source: str, target: str):
        self.edges[source] = target

    def add_conditional_edges(self, source: str, router: RouterFunction, mapping: dict[str, str]):
        self.conditional_edges[source] = (router, mapping)

    def set_entry_point(self, name: str):
        self.nodes[START] = None
        self.edges[START] = name

    def set_finish_point(self, name: str):
        self.add_edge(name, END)

    def compile(self, checkpointer=None, interrupt_before: list[str] | None = None, interrupt_after: list[str] | None = None):
        self.checkpointer = checkpointer
        self.interrupt_before = set(interrupt_before or [])
        self.interrupt_after = set(interrupt_after or [])
        compiled = CompiledGraph(self)
        return compiled


class CompiledGraph:
    def __init__(self, graph: GraphEngine):
        self._graph = graph
        self._checkpointer = graph.checkpointer

    def _next_node(self, state: State) -> str | None:
        current = state.get("_current_node", START)
        if current in self._graph.conditional_edges:
            router, mapping = self._graph.conditional_edges[current]
            route = router(state)
            return mapping.get(route, END)
        return self._graph.edges.get(current, END)

    async def invoke(self, state: State, thread_id: str | None = None) -> State:
        config = {"thread_id": thread_id} if thread_id else {}
        async for event in self._run(state, config):
            pass
        return event if event else state

    async def stream(self, state: State, thread_id: str | None = None) -> AsyncIterator[State]:
        config = {"thread_id": thread_id} if thread_id else {}
        async for event in self._run(state, config):
            yield event

    async def _run(self, state: State, config: dict) -> AsyncIterator[State]:
        if "_current_node" not in state:
            state["_current_node"] = START
        if "_interrupts" not in state:
            state["_interrupts"] = []
        if "_iteration" not in state:
            state["_iteration"] = 0

        if self._checkpointer:
            checkpoint = await self._checkpointer.get(config.get("thread_id", ""))
            if checkpoint:
                state = checkpoint
                logger.info("Resumed from checkpoint for thread %s", config.get("thread_id"))

        max_iterations = 50
        for _ in range(max_iterations):
            state["_iteration"] += 1
            current = state["_current_node"]

            if current == END:
                break

            if current == START:
                state["_current_node"] = self._graph.edges.get(START, END)
                if self._checkpointer:
                    await self._checkpointer.put(config.get("thread_id", ""), dict(state))
                continue

            node_fn = self._graph.nodes.get(current)
            if node_fn is None:
                raise ValueError(f"No node registered for '{current}'")

            if current in self._graph.interrupt_before and state.get("_interrupts"):
                logger.info("Interrupt before node %s", current)
                yield dict(state)
                if not state.get("_resume"):
                    return
                state["_resume"] = False

            node_name = current
            try:
                cmd = None
                result = node_fn(state)
                if hasattr(result, '__aiter__'):
                    async for item in result:
                        if isinstance(item, Command):
                            cmd = item
                        else:
                            yield item
                else:
                    res = await result
                    if isinstance(res, Command):
                        cmd = res
                    elif res is not None:
                        yield res

                if cmd:
                    state.update(cmd.update)
                    if cmd.subgraph:
                        sub = await cmd.subgraph.invoke(state, config.get("thread_id"))
                        state.update(sub)
                    if cmd.goto:
                        state["_current_node"] = cmd.goto
                    else:
                        next_n = self._next_node(state)
                        if next_n != current:
                            state["_current_node"] = next_n
                else:
                    next_n = self._next_node(state)
                    if next_n != current:
                        state["_current_node"] = next_n

            except Interrupt as exc:
                state["_interrupts"].append({"node": node_name, "value": exc.value})
                state["_current_node"] = END
                if self._checkpointer:
                    await self._checkpointer.put(config.get("thread_id", ""), dict(state))
                yield dict(state)
                return

            if current in self._graph.interrupt_after and state.get("_interrupts"):
                logger.info("Interrupt after node %s", current)
                yield dict(state)
                if not state.get("_resume"):
                    return
                state["_resume"] = False

            if self._checkpointer:
                await self._checkpointer.put(config.get("thread_id", ""), dict(state))

            yield dict(state)

        state["_current_node"] = END
        yield dict(state)

    async def get_state(self, thread_id: str) -> dict | None:
        if self._checkpointer:
            return await self._checkpointer.get(thread_id)
        return None
