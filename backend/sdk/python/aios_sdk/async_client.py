from __future__ import annotations
import httpx
from typing import Any, Optional


class AsyncAiosClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(base_url=self.base_url, headers=self._headers(), timeout=30)

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    async def health(self) -> dict:
        resp = await self._client.get("/api/v1/health")
        return resp.json()

    async def list_agents(self, project_id: Optional[str] = None) -> dict:
        params = {"project_id": project_id} if project_id else {}
        resp = await self._client.get("/api/v1/agents", params=params)
        return resp.json()

    async def get_agent(self, agent_id: str) -> dict:
        resp = await self._client.get(f"/api/v1/agents/{agent_id}")
        return resp.json()

    async def list_memory(self, project_id: str, limit: int = 50) -> dict:
        resp = await self._client.get(f"/api/v1/memory/{project_id}", params={"limit": limit})
        return resp.json()

    async def list_skills(self) -> dict:
        resp = await self._client.get("/api/v1/skills")
        return resp.json()

    async def metrics(self) -> dict:
        resp = await self._client.get("/api/v1/observability/metrics")
        return resp.json()

    async def close(self):
        await self._client.aclose()
