from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


async def run_onboarding(project_name: str = "", agent_name: str = "Coworker") -> dict:
    from app.services.agent_manager import agent_manager
    from app.config.loader import load_and_validate

    cfg, errors = load_and_validate()
    if errors:
        return {"ok": False, "errors": errors}

    project_id = None
    if not project_name:
        project_name = "My Project"

    from app.db.repository import save_project
    from app.models.project import Project
    project = Project(id=f"proj-{abs(hash(project_name)) % 10**8:08d}", title=project_name)
    await save_project(project)
    project_id = project.id

    boss = await agent_manager.create_coworker(project_id, name=agent_name)
    return {
        "ok": True,
        "project_id": project_id,
        "agent_id": boss.id,
        "config": cfg.to_dict(),
        "message": f"Onboarded project '{project_name}' with coworker '{agent_name}'.",
    }


def onboard_cli():
    import argparse
    parser = argparse.ArgumentParser(description="AIOS onboarding wizard")
    parser.add_argument("--project", default="", help="Project name")
    parser.add_argument("--agent", default="Coworker", help="Coworker agent name")
    args = parser.parse_args()
    result = asyncio.run(run_onboarding(args.project, args.agent))
    if result.get("ok"):
        print(result["message"])
        print(f"  project_id: {result['project_id']}")
        print(f"  agent_id:   {result['agent_id']}")
    else:
        print("Onboarding failed:")
        for e in result.get("errors", []):
            print(f"  - {e}")
