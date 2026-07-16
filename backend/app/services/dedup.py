import asyncio
import logging
from collections import defaultdict

from app.db.repository import load_project_agents, merge_agents, load_project
from app.db.session import async_session
from app.db.models import ProjectModel, AgentModel
from sqlalchemy import select
from app.models.agent import normalize_name

logger = logging.getLogger(__name__)


async def deduplicate_all_projects():
    """Scan every project, merge duplicate agents into canonical singletons."""
    logger.info("Dedup: Starting project scan for duplicate agents...")
    async with async_session() as s:
        result = await s.execute(select(ProjectModel.id))
        project_ids = [row[0] for row in result.fetchall()]

    for pid in project_ids:
        await deduplicate_project(pid)

    logger.info("Dedup: Finished scanning %d projects.", len(project_ids))


async def deduplicate_project(project_id: str):
    """Merge duplicate agents within a single project."""
    agents = await load_project_agents(project_id)
    if len(agents) < 2:
        return

    # Group by normalized_name
    groups = defaultdict(list)
    for a in agents:
        norm = a.normalized_name or normalize_name(a.name)
        groups[norm].append(a)

    merged_count = 0
    for norm, group in groups.items():
        if len(group) < 2:
            continue
        # Sort by created_at, keep the oldest as survivor
        group.sort(key=lambda a: a.created_at or "")
        survivor = group[0]
        logger.info("Dedup: Project %s — found %d agents with name '%s'. Keeping %s, merging others.",
                     project_id, len(group), survivor.name, survivor.id)

        for duplicate in group[1:]:
            try:
                await merge_agents(survivor.id, duplicate.id, project_id)
                merged_count += 1
                logger.info("Dedup: Merged %s (%s) into %s (%s)", duplicate.name, duplicate.id, survivor.name, survivor.id)
            except Exception as e:
                logger.warning("Dedup: Failed to merge %s into %s: %s", duplicate.id, survivor.id, e)

    if merged_count:
        logger.info("Dedup: Project %s — merged %d duplicate agents.", project_id, merged_count)
