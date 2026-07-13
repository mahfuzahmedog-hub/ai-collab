from __future__ import annotations
import re
from typing import Any


class GeneralChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[dict[str, Any]]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                break_at = max(
                    text.rfind(". ", start, end),
                    text.rfind("\n\n", start, end),
                    text.rfind(" ", start, end),
                )
                if break_at > start:
                    end = break_at + 1
            content = text[start:end].strip()
            if content:
                chunks.append({"content": content, "index": len(chunks), "start": start, "end": end})
            start = end - self.overlap
        return chunks


class ParentChildChunker:
    def __init__(self, parent_size: int = 2000, child_size: int = 500, overlap: int = 50):
        self.parent_chunker = GeneralChunker(parent_size, overlap)
        self.child_chunker = GeneralChunker(child_size, overlap)

    def chunk(self, text: str) -> list[dict[str, Any]]:
        parents = self.parent_chunker.chunk(text)
        result = []
        for parent in parents:
            children = self.child_chunker.chunk(parent["content"])
            result.append({
                "content": parent["content"],
                "index": parent["index"],
                "type": "parent",
                "children": children,
                "child_count": len(children),
            })
        return result


class QAChunker:
    def __init__(self, min_question_words: int = 3):
        self.min_question_words = min_question_words

    def chunk(self, text: str) -> list[dict[str, Any]]:
        pairs = []
        lines = text.split("\n")
        current_q = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.endswith("?") or re.match(r'^(Q|Question):', line, re.IGNORECASE):
                if current_q:
                    pairs.append({"question": current_q["question"], "answer": current_q["answer"].strip()})
                clean_q = re.sub(r'^(Q|Question):\s*', '', line, flags=re.IGNORECASE)
                current_q = {"question": clean_q, "answer": ""}
            elif current_q:
                current_q["answer"] += line + "\n"
        if current_q and current_q["answer"].strip():
            pairs.append({"question": current_q["question"], "answer": current_q["answer"].strip()})
        return pairs
