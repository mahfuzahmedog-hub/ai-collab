from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemoryBlock:
    id: str
    name: str
    content: str
    system_flag: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def to_frontmatter(self) -> str:
        parts = ["---"]
        parts.append(f"id: {self.id}")
        parts.append(f"name: {self.name}")
        parts.append(f"system: {str(self.system_flag).lower()}")
        if self.tags:
            parts.append(f"tags: [{', '.join(self.tags)}]")
        if self.metadata:
            for k, v in self.metadata.items():
                parts.append(f"{k}: {v}")
        parts.append(f"version: {self.version}")
        parts.append(f"updated_at: {self.updated_at or datetime.utcnow().isoformat() + 'Z'}")
        parts.append("---")
        parts.append("")
        parts.append(self.content)
        return "\n".join(parts)

    @classmethod
    def from_frontmatter(cls, text: str) -> MemoryBlock:
        import yaml, re
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
        if not match:
            return cls(id="", name="unknown", content=text)
        meta = yaml.safe_load(match.group(1)) or {}
        content = match.group(2).strip()
        return cls(
            id=meta.get("id", ""),
            name=meta.get("name", "unknown"),
            content=content,
            system_flag=meta.get("system", False),
            tags=meta.get("tags", []),
            metadata={k: v for k, v in meta.items() if k not in ("id", "name", "system", "tags", "version", "updated_at")},
            version=meta.get("version", 1),
            updated_at=meta.get("updated_at", ""),
        )

    def __len__(self):
        return len(self.content)

    def __str__(self):
        return f"[{self.id}] {self.name} ({len(self)} chars)"
