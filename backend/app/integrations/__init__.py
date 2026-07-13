from __future__ import annotations
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class IntegrationAdapter:
    def __init__(self, name: str):
        self.name = name

    async def execute(self, action: str, params: dict) -> dict:
        raise NotImplementedError


class HTTPIntegration(IntegrationAdapter):
    def __init__(self, name: str, base_url: str, headers: dict = None):
        super().__init__(name)
        self.base_url = base_url
        self.headers = headers or {}

    async def execute(self, action: str, params: dict) -> dict:
        import httpx
        method = params.get("method", "GET")
        url = self.base_url + params.get("path", "")
        try:
            resp = await httpx.request(method, url, headers=self.headers, json=params.get("body"), timeout=30)
            return {"status": resp.status_code, "body": resp.text[:5000]}
        except Exception as e:
            return {"error": str(e)}


class IntegrationRegistry:
    def __init__(self):
        self._integrations: dict[str, IntegrationAdapter] = {}

    def register(self, integration: IntegrationAdapter):
        self._integrations[integration.name] = integration
        logger.info("Registered integration: %s", integration.name)

    def get(self, name: str) -> Optional[IntegrationAdapter]:
        return self._integrations.get(name)

    def list(self) -> list[str]:
        return list(self._integrations.keys())


integration_registry = IntegrationRegistry()


async def register_default_integrations():
    integration_registry.register(HTTPIntegration("github", "https://api.github.com", headers={"Accept": "application/vnd.github+json"}))
    integration_registry.register(HTTPIntegration("slack", "https://slack.com/api"))
    integration_registry.register(HTTPIntegration("notion", "https://api.notion.com/v1"))
