import asyncio
import logging
from typing import Optional

from app.db.repository import save_agent, load_project_agents, find_existing_agent, get_or_create_agent, merge_agents
from app.models.agent import Agent, AgentStatus, normalize_name

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Per-project central registry. All agent creation must go through here."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._lock = asyncio.Lock()
        self._agents_by_id: dict[str, Agent] = {}
        self._agents_by_norm: dict[str, str] = {}  # normalized_name -> id

    async def load_from_db(self):
        """Populate in-memory cache from database."""
        agents = await load_project_agents(self.project_id)
        self._agents_by_id.clear()
        self._agents_by_norm.clear()
        for a in agents:
            self._agents_by_id[a.id] = a
            norm = a.normalized_name or normalize_name(a.name)
            self._agents_by_norm[norm] = a.id

    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        return self._agents_by_id.get(agent_id)

    async def find_by_normalized_name(self, name: str) -> Optional[Agent]:
        norm = normalize_name(name)
        aid = self._agents_by_norm.get(norm)
        if aid:
            return self._agents_by_id.get(aid)
        return await find_existing_agent(self.project_id, normalized_name=norm)

    async def find_or_create(self, spec: dict) -> tuple[Agent, bool]:
        """Find matching agent or create one. Returns (agent, is_new)."""
        from app.core.config import settings

        name = spec.get("name", "Unnamed")
        role = spec.get("role", "engineer")
        specialization = spec.get("specialization", "")
        norm = normalize_name(name)

        logger.info("AgentRegistry [%s]: Checking for existing agent (role=%s, specialization=%s, name=%s)",
                     self.project_id, role, specialization, name)

        # Check in-memory cache first (fast path, no DB call)
        existing_id = self._agents_by_norm.get(norm)
        if existing_id:
            existing = self._agents_by_id.get(existing_id)
            if existing:
                logger.info("AgentRegistry [%s]: Existing agent found in cache. Reusing agent %s.", self.project_id, existing.name)
                return existing, False

        # Serialize concurrent creation per project
        async with self._lock:
            # Double-check after acquiring lock
            existing_id = self._agents_by_norm.get(norm)
            if existing_id:
                existing = self._agents_by_id.get(existing_id)
                if existing:
                    logger.info("AgentRegistry [%s]: Existing agent found (after lock). Reusing agent %s.", self.project_id, existing.name)
                    return existing, False

            # Check database
            existing = await find_existing_agent(
                self.project_id,
                normalized_name=norm,
                role=role,
                specialization=specialization,
            )
            if existing:
                self._agents_by_id[existing.id] = existing
                self._agents_by_norm[existing.normalized_name or normalize_name(existing.name)] = existing.id
                logger.info("AgentRegistry [%s]: Existing agent found in DB. Reusing agent %s.", self.project_id, existing.name)
                return existing, False

            logger.info("AgentRegistry [%s]: No existing agent found. Creating new agent '%s'.", self.project_id, name)

            agent = Agent(
                name=name,
                normalized_name=norm,
                specialization=specialization,
                role=role,
                project_id=self.project_id,
                skills=spec.get("skills", [role]),
                personality=spec.get("personality", "professional and collaborative"),
                display_name=spec.get("display_name") or name,
                mission=spec.get("mission", ""),
                channel=spec.get("channel") or "general",
                provider=spec.get("provider") or settings.llm_default_provider,
                model=spec.get("model") or settings.llm_default_model,
            )

            created_agent, is_new = await get_or_create_agent(self.project_id, agent)
            self._agents_by_id[created_agent.id] = created_agent
            self._agents_by_norm[created_agent.normalized_name or normalize_name(created_agent.name)] = created_agent.id

            if is_new:
                logger.info("AgentRegistry [%s]: Saved new agent %s (%s).", self.project_id, created_agent.name, created_agent.id)
            else:
                logger.info("AgentRegistry [%s]: Race resolved — agent %s already existed.", self.project_id, created_agent.name)

            return created_agent, is_new

    async def remove(self, agent_id: str):
        self._agents_by_id.pop(agent_id, None)
        # Clean up reverse lookup
        for norm, aid in list(self._agents_by_norm.items()):
            if aid == agent_id:
                self._agents_by_norm.pop(norm, None)
                break

    def get_all(self) -> list[Agent]:
        return list(self._agents_by_id.values())
