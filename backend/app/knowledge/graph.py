from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    def __init__(self):
        self._entities: dict[str, dict] = {}
        self._relationships: list[dict] = []
        self._adjacency: dict[str, list[dict]] = {}

    def add_entity(self, name: str, entity_type: str, description: str = "", metadata: Optional[dict] = None) -> str:
        key = name.lower().strip()
        if key not in self._entities:
            self._entities[key] = {
                "name": name, "type": entity_type, "description": description,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat() + "Z",
                "access_count": 0,
            }
            self._adjacency[key] = []
        else:
            self._entities[key]["access_count"] += 1
            if description:
                self._entities[key]["description"] = description
        return key

    def add_relationship(self, source: str, target: str, rel_type: str, description: str = "") -> bool:
        sk = source.lower().strip()
        tk = target.lower().strip()
        if sk not in self._entities or tk not in self._entities:
            return False
        rel = {
            "source": sk, "target": tk, "type": rel_type,
            "description": description,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        self._relationships.append(rel)
        self._adjacency.setdefault(sk, []).append(rel)
        self._adjacency.setdefault(tk, []).append(rel)
        return True

    def get_entity(self, name: str) -> Optional[dict]:
        key = name.lower().strip()
        ent = self._entities.get(key)
        if ent:
            ent["access_count"] += 1
        return ent

    def query(self, entity_name: str, max_depth: int = 2) -> dict:
        key = entity_name.lower().strip()
        if key not in self._entities:
            return {"entity": None, "relations": []}
        visited = set()
        results = []

        def dfs(current: str, depth: int):
            if depth > max_depth or current in visited:
                return
            visited.add(current)
            for rel in self._adjacency.get(current, []):
                other = rel["target"] if rel["source"] == current else rel["source"]
                results.append({
                    "source": rel["source"], "target": rel["target"],
                    "type": rel["type"], "description": rel.get("description", ""),
                })
                if other not in visited:
                    dfs(other, depth + 1)

        dfs(key, 0)
        return {"entity": self._entities[key], "relations": results}

    def traverse(self, entity_name: str, rel_type: Optional[str] = None) -> list[dict]:
        key = entity_name.lower().strip()
        results = []
        for rel in self._adjacency.get(key, []):
            if rel_type and rel["type"] != rel_type:
                continue
            other = rel["target"] if rel["source"] == key else rel["source"]
            results.append({"entity": self._entities.get(other), "relationship": rel})
        return results

    def get_all_entities(self) -> list[dict]:
        return list(self._entities.values())

    def get_all_relationships(self) -> list[dict]:
        return list(self._relationships)

    def to_dict(self) -> dict:
        return {
            "entities": self.get_all_entities(),
            "relationships": self.get_all_relationships(),
        }

    def merge(self, other: KnowledgeGraph):
        for ent in other.get_all_entities():
            self.add_entity(ent["name"], ent["type"], ent.get("description", ""), ent.get("metadata"))
        for rel in other.get_all_relationships():
            self.add_relationship(rel["source"], rel["target"], rel["type"], rel.get("description", ""))


knowledge_graph = KnowledgeGraph()
