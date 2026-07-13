from __future__ import annotations
import httpx
from typing import Any, Optional


class AiosClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(base_url=self.base_url, headers=self._headers(), timeout=30)

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def health(self) -> dict:
        return self._client.get("/api/v1/health").json()

    def list_agents(self, project_id: Optional[str] = None) -> dict:
        params = {"project_id": project_id} if project_id else {}
        return self._client.get("/api/v1/agents", params=params).json()

    def get_agent(self, agent_id: str) -> dict:
        return self._client.get(f"/api/v1/agents/{agent_id}").json()

    def list_memory(self, project_id: str, limit: int = 50) -> dict:
        return self._client.get(f"/api/v1/memory/{project_id}", params={"limit": limit}).json()

    def list_skills(self) -> dict:
        return self._client.get("/api/v1/skills").json()

    def list_sessions(self, project_id: Optional[str] = None) -> dict:
        params = {"project_id": project_id} if project_id else {}
        return self._client.get("/api/v1/sessions", params=params).json()

    def metrics(self) -> dict:
        return self._client.get("/api/v1/observability/metrics").json()

    def list_integrations(self) -> dict:
        return self._client.get("/api/v1/integrations").json()

    def list_mcp_servers(self) -> dict:
        return self._client.get("/api/v1/mcp/servers").json()

    def list_plugins(self) -> dict:
        return self._client.get("/api/v1/plugins").json()

    def close(self):
        self._client.close()
