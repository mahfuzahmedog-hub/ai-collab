from __future__ import annotations
import json
import logging
import re
from typing import Any

from app.llm import llm_router

logger = logging.getLogger(__name__)


class EntityExtractor:
    def __init__(self):
        pass

    async def extract(self, text: str) -> dict[str, Any]:
        prompt = f"""Extract entities and relationships from this text:

{text[:2000]}

Return JSON:
{{
  "entities": [{{"name": "...", "type": "person|concept|project|tool", "description": "..."}}],
  "relationships": [{{"source": "...", "target": "...", "type": "works_on|uses|part_of|related_to", "description": "..."}}]
}}

Only include clearly stated information. Return empty lists if nothing found."""
        provider = llm_router.get_provider()
        if not provider:
            return {"entities": [], "relationships": []}
        try:
            response = await provider.chat([
                {"role": "system", "content": "Extract structured knowledge from text."},
                {"role": "user", "content": prompt},
            ], temperature=0.2)
            return self._parse(response)
        except Exception as e:
            logger.warning("Entity extraction failed: %s", e)
            return {"entities": [], "relationships": []}

    def _parse(self, text: str) -> dict:
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return {"entities": [], "relationships": []}


entity_extractor = EntityExtractor()
