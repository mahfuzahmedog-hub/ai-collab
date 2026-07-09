import os
import logging
from pathlib import Path
from typing import List, Dict, Any

from app.core.event_bus import event_bus
from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent.parent.parent / "workspace"

def _project_dir(project_id: str) -> Path:
    return BASE_DIR / project_id

def _ensure_project_dir(project_id: str) -> Path:
    proj_dir = _project_dir(project_id)
    proj_dir.mkdir(parents=True, exist_ok=True)
    return proj_dir

async def write_file(project_id: str, path: str, content: str) -> Dict[str, Any]:
    proj_dir = _ensure_project_dir(project_id)
    full_path = proj_dir / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    full_path.write_text(content, encoding="utf-8")
    
    stat = full_path.stat()
    event = {
        "type": "file_changed",
        "project_id": project_id,
        "path": path,
        "action": "write",
        "size": stat.st_size,
        "timestamp": stat.st_mtime,
    }
    await event_bus.publish("file_changed", event)
    
    return {"path": path, "size": stat.st_size, "modified": stat.st_mtime}

async def read_file(project_id: str, path: str) -> str:
    full_path = _project_dir(project_id) / path
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return full_path.read_text(encoding="utf-8")

async def list_files(project_id: str) -> List[Dict[str, Any]]:
    proj_dir = _project_dir(project_id)
    if not proj_dir.exists():
        return []
    
    results = []
    for root, dirs, files in os.walk(proj_dir):
        rel_root = Path(root).relative_to(proj_dir)
        for f in files:
            full = Path(root) / f
            rel = rel_root / f
            stat = full.stat()
            results.append({
                "path": str(rel),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_dir": False,
            })
        for d in dirs:
            full = Path(root) / d
            rel = rel_root / d
            stat = full.stat()
            results.append({
                "path": str(rel) + "/",
                "size": 0,
                "modified": stat.st_mtime,
                "is_dir": True,
            })
    return sorted(results, key=lambda x: x["path"])

async def get_file_tree(project_id: str) -> List[Dict[str, Any]]:
    files = await list_files(project_id)
    tree: Dict[str, Any] = {"name": "", "path": "", "type": "directory", "children": {}, "modified": 0}
    
    for f in files:
        parts = Path(f["path"]).parts
        node = tree
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            if part not in node["children"]:
                node["children"][part] = {
                    "name": part,
                    "path": str(Path(*parts[:i+1])),
                    "type": "file" if is_last and not f["is_dir"] else "directory",
                    "children": {} if not (is_last and not f["is_dir"]) else None,
                    "size": f["size"] if is_last and not f["is_dir"] else 0,
                    "modified": f["modified"],
                }
            node = node["children"][part]
    
    def to_list(node: Dict[str, Any]) -> Dict[str, Any]:
        if node.get("children") is None:
            return node
        return {
            "name": node["name"],
            "path": node["path"],
            "type": node["type"],
            "size": node.get("size", 0),
            "modified": node["modified"],
            "children": [to_list(child) for child in node["children"].values()],
        }
    
    root = to_list(tree)
    return root["children"] if root.get("children") else []