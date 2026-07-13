from __future__ import annotations
from typing import Optional
from app.tools.registry import tool_registry


def build_system_prompt(
    name: str,
    role: str,
    personality: str,
    skills: list[str],
    project_id: str,
    mission: str = "",
    extra_sections: Optional[list[str]] = None,
) -> str:
    parts = [
        f"You are {name}, a {role} in an AI collaboration team.",
        f"Personality: {personality}",
        f"Skills: {', '.join(skills)}",
        f"You are working on project {project_id}.",
        "",
        "Communicate naturally with your teammates like a human coworker.",
        "Be concise, professional, and collaborative.",
        "You can ask questions, suggest ideas, report progress, request reviews, and help others.",
    ]
    if mission:
        parts.insert(3, f"Mission: {mission}")
    if extra_sections:
        parts.extend(extra_sections)
    return "\n".join(parts)


def build_tools_block(with_tools: bool = True) -> str:
    if not with_tools:
        return ""
    schemas = tool_registry.to_openai_schemas()
    if not schemas:
        return ""
    lines = ["", "<available_tools>"]
    for s in schemas:
        lines.append(f"- {s['function']['name']}: {s['function']['description']}")
    lines.append("</available_tools>")
    lines.append("")
    lines.append("To use a tool, respond with a JSON tool_call. The system will execute it and return the result.")
    return "\n".join(lines)


def build_memories_block(memories: list[dict]) -> str:
    if not memories:
        return ""
    lines = ["", "<recalled_memories>"]
    for m in memories:
        content = m.get("content", "")[:200]
        type_tag = m.get("type", "fact")
        lines.append(f"[{type_tag}] {content}")
    lines.append("</recalled_memories>")
    return "\n".join(lines)


def build_skills_block(skills_text: str) -> str:
    return skills_text
