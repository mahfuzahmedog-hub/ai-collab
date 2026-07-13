from __future__ import annotations
import asyncio
import logging
from typing import Optional

from app.curation.evaluator import evaluate_exchange
from app.memory.manager import memory_manager

logger = logging.getLogger(__name__)

_CONSOLIDATE_INTERVAL = 25
_PRUNE_IMPORTANCE_THRESHOLD = 0.2
_PRUNE_MAX_MEMORIES = 500
_curation_counter = 0


async def run_curation_loop(
    user_msg: str,
    agent_resp: str,
    project_id: str,
    agent_id: str,
    llm_provider=None,
):
    global _curation_counter
    _curation_counter += 1

    eval_result = evaluate_exchange(user_msg, agent_resp)

    if eval_result["should_create_skill"]:
        asyncio.create_task(_maybe_create_skill(
            user_msg, agent_resp, llm_provider, eval_result["suggested_category"],
        ))

    if _curation_counter % _CONSOLIDATE_INTERVAL == 0:
        asyncio.create_task(_consolidate_and_prune(project_id))


async def _maybe_create_skill(
    user_msg: str,
    agent_resp: str,
    llm_provider=None,
    category: Optional[str] = None,
):
    from app.skills.creator import create_skill_from_conversation
    try:
        skill_id = await create_skill_from_conversation(
            user_msg, agent_resp, llm_provider=llm_provider,
        )
        if skill_id:
            logger.info("Curator created skill %s", skill_id)
    except Exception as e:
        logger.warning("Curator skill creation failed: %s", e)


async def _consolidate_and_prune(project_id: str):
    try:
        merged = await memory_manager.consolidate(project_id)
        if merged:
            logger.info("Curator consolidated %d memories", merged)
        pruned = await memory_manager.prune(
            project_id=project_id,
            importance_threshold=_PRUNE_IMPORTANCE_THRESHOLD,
            max_memories=_PRUNE_MAX_MEMORIES,
        )
        if pruned:
            logger.info("Curator pruned %d low-importance memories", pruned)
    except Exception as e:
        logger.warning("Curator consolidate/prune failed: %s", e)
