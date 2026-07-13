from __future__ import annotations
import json
import logging
from typing import Optional

from app.curation.evaluator import evaluate_exchange
from app.curation.profile import UserProfile, get_user_profile, save_user_profile
from app.memory.manager import memory_manager

logger = logging.getLogger(__name__)


async def run_llm_curation(
    user_id: str,
    project_id: str,
    agent_id: str,
    user_msg: str,
    agent_resp: str,
    llm_provider=None,
):
    eval_result = evaluate_exchange(user_msg, agent_resp)
    profile = await get_user_profile(user_id, project_id)
    profile.update_from_conversation(user_msg)
    await save_user_profile(profile)
    if eval_result["importance"] >= 0.7:
        await memory_manager.save({
            "type": "fact",
            "content": user_msg[:500],
            "scope": "project",
            "source": "curation",
            "project_id": project_id,
            "agent_id": agent_id,
            "importance": eval_result["importance"],
            "tags": eval_result.get("memory_tags", ["curation"]),
        })
    if eval_result["should_create_skill"]:
        from app.skills.creator import create_skill_from_conversation
        try:
            await create_skill_from_conversation(
                user_msg, agent_resp, llm_provider=llm_provider,
            )
        except Exception as e:
            logger.warning("LLM curation skill creation failed: %s", e)
