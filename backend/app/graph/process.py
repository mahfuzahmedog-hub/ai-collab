from __future__ import annotations
import asyncio
import logging
from enum import Enum
from typing import Any, Optional

from app.graph.engine import GraphEngine, START, END
from app.graph.types import Command

logger = logging.getLogger(__name__)


class ProcessType(Enum):
    sequential = "sequential"
    hierarchical = "hierarchical"


class SequentialProcess:
    def __init__(self, tasks: list[dict]):
        self.tasks = tasks
        self.current_index = 0

    def build_graph(self, worker_fn) -> GraphEngine:
        builder = GraphEngine()
        builder.set_entry_point("sequential_router")

        async def sequential_router(state: dict) -> Command:
            idx = state.get("_task_index", 0)
            if idx < len(self.tasks):
                return Command(update={"_task_index": idx + 1, "_current_task": self.tasks[idx]}, goto="process_task")
            return Command(goto=END)

        async def process_task(state: dict) -> Command:
            task = state.get("_current_task", {})
            result = await worker_fn(task, state)
            updates = {"_last_result": result}
            updates.setdefault("_results", []).append(result)
            return Command(update=updates)

        builder.add_node("sequential_router", sequential_router)
        builder.add_node("process_task", process_task)
        builder.add_edge("process_task", "sequential_router")
        return builder


class HierarchicalProcess:
    def __init__(self, manager_node: str, worker_nodes: list[str]):
        self.manager_node = manager_node
        self.worker_nodes = worker_nodes

    def build_graph(self, manager_fn, worker_fns: dict[str, callable]) -> GraphEngine:
        builder = GraphEngine()
        builder.set_entry_point("manager_node")

        async def manager_wrapper(state: dict) -> Command:
            result = await manager_fn(state)
            cmd = result if isinstance(result, Command) else Command(update={"manager_output": result})
            if cmd.goto and cmd.goto in self.worker_nodes:
                return cmd
            return Command(goto="manager_node")

        builder.add_node("manager_node", manager_wrapper)
        for wn in self.worker_nodes:
            fn = worker_fns.get(wn)
            if fn:
                builder.add_node(wn, fn)
                builder.add_edge(wn, "manager_node")

        return builder
