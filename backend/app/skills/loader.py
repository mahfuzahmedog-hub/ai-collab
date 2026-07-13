from __future__ import annotations
import logging
from app.memory.manager import memory_manager

logger = logging.getLogger(__name__)

_MAX_SKILL_TOKENS = 1500


async def find_matching_skills(message: str, category: Optional[str] = None) -> list[dict]:
    if not message or not message.strip():
        return []
    skills = await memory_manager.list_skills(category=category, limit=50)
    msg_lower = message.lower()
    matched = []
    for skill in skills:
        for phrase in skill.get("trigger_phrases", []):
            if phrase.lower() in msg_lower:
                matched.append(skill)
                break
    if not matched:
        results = await memory_manager.search_skills(message, category=category, limit=3)
        matched.extend(results)
    return matched


async def load_skills_for_prompt(message: str, category: Optional[str] = None) -> str:
    skills = await find_matching_skills(message, category)
    if not skills:
        return ""
    lines = ["<relevant_skills>"]
    token_budget = _MAX_SKILL_TOKENS
    for skill in skills:
        tmpl = skill.get("prompt_template", "") or skill.get("description", "")
        if not tmpl:
            continue
        estimated = len(tmpl.split())
        if estimated > token_budget:
            tmpl = " ".join(tmpl.split()[:token_budget]) + " [truncated]"
        lines.append(f'- **{skill["name"]}** ({skill.get("category", "knowledge")}): {tmpl}')
        token_budget -= estimated
        if token_budget <= 0:
            break
    lines.append("</relevant_skills>")
    return "\n".join(lines)
