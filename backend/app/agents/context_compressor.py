from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_BUDGET_SYSTEM = 0.25
_BUDGET_HISTORY = 0.50
_BUDGET_NEW = 0.25
_MAX_TOTAL_TOKENS = 8192


def estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


def compress_history(
    history: list[dict],
    max_tokens: int = _MAX_TOTAL_TOKENS,
) -> list[dict]:
    if not history:
        return history
    total = sum(estimate_tokens(m.get("content", "")) for m in history)
    if total <= int(max_tokens * _BUDGET_HISTORY):
        return history
    budget = int(max_tokens * _BUDGET_HISTORY)
    compressed = []
    running = 0
    for m in reversed(history):
        tokens = estimate_tokens(m.get("content", ""))
        if running + tokens <= budget:
            compressed.insert(0, m)
            running += tokens
        else:
            break
    if len(compressed) < len(history):
        summary = _summarize_turns(history[:len(history) - len(compressed)])
        if summary:
            compressed.insert(0, {"role": "system", "content": f"[Compressed earlier conversation: {summary}]"})
    return compressed


def _summarize_turns(turns: list[dict]) -> str:
    if not turns:
        return ""
    n = len(turns)
    topics = set()
    for t in turns:
        content = (t.get("content") or "")[:100]
        if any(kw in content.lower() for kw in ["bug", "error", "fix", "issue"]):
            topics.add("bugfix")
        elif any(kw in content.lower() for kw in ["feature", "add", "implement", "new"]):
            topics.add("feature")
        elif any(kw in content.lower() for kw in ["how", "what", "why", "explain"]):
            topics.add("question")
    topic_str = ", ".join(topics) if topics else "general discussion"
    return f"{n} previous turns about {topic_str}"
