from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class NodeType(Enum):
    llm = "llm"
    agent = "agent"
    tool = "tool"
    code = "code"
    webhook = "webhook"
    schedule = "schedule"
    if_node = "if"
    loop = "loop"
    http = "http"
    function = "function"
    subworkflow = "subworkflow"
    input = "input"
    output = "output"


class WorkflowStatus(Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    archived = "archived"


@dataclass
class WorkflowNode:
    id: str
    type: NodeType
    config: dict[str, Any] = field(default_factory=dict)
    position: dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})


@dataclass
class WorkflowEdge:
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    condition: Optional[str] = None


@dataclass
class Workflow:
    id: str
    name: str
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.draft
    trigger: str = "manual"
    project_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    owner_id: str = ""

    def add_node(self, node: WorkflowNode):
        self.nodes.append(node)

    def add_edge(self, edge: WorkflowEdge):
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        return next((n for n in self.nodes if n.id == node_id), None)

    def entry_nodes(self) -> list[WorkflowNode]:
        source_ids = {e.source for e in self.edges}
        return [n for n in self.nodes if n.id not in source_ids]

    def outgoing(self, node_id: str) -> list[WorkflowEdge]:
        return [e for e in self.edges if e.source == node_id]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name,
            "nodes": [{"id": n.id, "type": n.type.value, "config": n.config, "position": n.position} for n in self.nodes],
            "edges": [{"id": e.id, "source": e.source, "target": e.target, "condition": e.condition} for e in self.edges],
            "status": self.status.value, "trigger": self.trigger,
            "project_id": self.project_id, "owner_id": self.owner_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Workflow:
        wf = cls(
            id=d.get("id", ""), name=d.get("name", ""),
            status=WorkflowStatus(d.get("status", "draft")),
            trigger=d.get("trigger", "manual"),
            project_id=d.get("project_id", ""), owner_id=d.get("owner_id", ""),
        )
        for n in d.get("nodes", []):
            wf.add_node(WorkflowNode(id=n["id"], type=NodeType(n["type"]), config=n.get("config", {}), position=n.get("position", {"x": 0, "y": 0})))
        for e in d.get("edges", []):
            wf.add_edge(WorkflowEdge(id=e.get("id", ""), source=e["source"], target=e["target"], condition=e.get("condition")))
        return wf
