from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Optional
from app.skills.models import Skill

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.utcnow().isoformat() + "Z"


def build_skill_from_data(data: dict) -> Skill:
    return Skill(
        name=data.get("name", ""),
        description=data.get("description", ""),
        category=data.get("category", "knowledge"),
        prompt_template=data.get("prompt_template", ""),
        trigger_phrases=data.get("trigger_phrases", []),
        parameters=data.get("parameters", {}),
        metadata=data.get("metadata", {}),
    )


def parse_skill_from_llm_response(llm_text: str) -> Optional[Skill]:
    import re
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", llm_text, re.DOTALL)
    if not json_match:
        json_match = re.search(r"\{[^{}]*\"name\"[^{}]*\}", llm_text, re.DOTALL)
    if not json_match:
        logger.warning("No valid skill JSON found in LLM response")
        return None
    try:
        data = json.loads(json_match.group(1) if json_match.groups() else json_match.group(0))
    except (json.JSONDecodeError, IndexError):
        return None
    return build_skill_from_data(data)


async def create_skill_from_conversation(
    user_message: str,
    agent_response: str,
    conversation_history: Optional[list[dict]] = None,
    llm_provider=None,
) -> Optional[str]:
    from app.memory.manager import memory_manager

    existing = await memory_manager.get_skill_by_name(_derive_name(user_message))
    if existing:
        logger.info("Skill '%s' already exists, skipping", existing["name"])
        return existing["id"]

    prompt = f"""You are a skill extraction system. Based on the following conversation, create a reusable skill definition.

User: {user_message[:2000]}
Agent: {agent_response[:2000]}

Extract the reusable pattern as JSON:
{{
  "name": "short-kebab-case-name",
  "description": "one-line summary",
  "category": "workflow|knowledge|template|integration",
  "prompt_template": "instructions for when this skill is triggered",
  "trigger_phrases": ["key phrases that should activate this skill"]
}}
Respond ONLY with the JSON object, no other text."""

    if llm_provider and hasattr(llm_provider, "chat"):
        try:
            resp = await llm_provider.chat([{"role": "user", "content": prompt}])
            text = resp.get("content", "")
        except Exception as e:
            logger.warning("LLM skill creation failed: %s", e)
            return None
    else:
        text = _fallback_extract(user_message, agent_response)

    skill = parse_skill_from_llm_response(text)
    if not skill:
        logger.warning("Failed to parse skill from LLM response")
        return None

    skill_id = await memory_manager.save_skill(skill.model_dump())
    logger.info("Created skill '%s' (%s)", skill.name, skill_id)
    return skill_id


def _derive_name(msg: str) -> str:
    words = msg.lower().split()[:4]
    return "-".join(w for w in words if w.isalpha())[:50]


def _fallback_extract(user_msg: str, agent_resp: str) -> str:
    words = user_msg.split()
    name = "-".join(w.lower() for w in words[:3] if w.isalpha())
    desc = user_msg[:120]
    trigger = words[:5]
    skill_data = {
        "name": name or "extracted-skill",
        "description": desc,
        "category": "workflow",
        "prompt_template": f"When asked about {desc[:80]}, follow this approach:\n{agent_resp[:500]}",
        "trigger_phrases": trigger,
    }
    return json.dumps(skill_data, indent=2)
