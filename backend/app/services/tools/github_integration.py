import os
import logging

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"


def _token() -> str:
    from app.core.config import settings
    return settings.github_token or os.environ.get("GITHUB_TOKEN", "")


def _headers() -> dict:
    h = {"Accept": "application/vnd.github.v3+json", "User-Agent": "aios-agent"}
    tok = _token()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


async def get_repo(owner: str, repo: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as cl:
            r = await cl.get(f"{_GITHUB_API}/repos/{owner}/{repo}", headers=_headers())
            r.raise_for_status()
            d = r.json()
            return {
                "name": d.get("full_name"),
                "description": d.get("description"),
                "stars": d.get("stargazers_count", 0),
                "forks": d.get("forks_count", 0),
                "language": d.get("language"),
                "topics": d.get("topics", []),
                "error": None,
            }
    except Exception as e:
        return {"error": str(e)}


async def search_repos(query: str, limit: int = 5) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as cl:
            r = await cl.get(
                f"{_GITHUB_API}/search/repositories",
                params={"q": query, "per_page": limit},
                headers=_headers(),
            )
            r.raise_for_status()
            items = r.json().get("items", [])
            return [
                {
                    "name": i.get("full_name"),
                    "description": i.get("description"),
                    "stars": i.get("stargazers_count", 0),
                    "language": i.get("language"),
                    "url": i.get("html_url"),
                }
                for i in items
            ]
    except Exception as e:
        return [{"error": str(e)}]


async def get_file_content(owner: str, repo: str, path: str, branch: str = "main") -> dict:
    try:
        async with httpx.AsyncClient(timeout=15) as cl:
            r = await cl.get(
                f"{_GITHUB_API}/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
                headers=_headers(),
            )
            r.raise_for_status()
            d = r.json()
            import base64
            if d.get("encoding") == "base64":
                content = base64.b64decode(d["content"]).decode("utf-8")
            else:
                content = d.get("content", "")
            return {"path": d.get("path"), "content": content, "size": d.get("size"), "error": None}
    except Exception as e:
        return {"error": str(e)}


async def create_issue(owner: str, repo: str, title: str, body: str = "") -> dict:
    tok = _token()
    if not tok:
        return {"error": "GITHUB_TOKEN not configured"}
    try:
        async with httpx.AsyncClient(timeout=15) as cl:
            r = await cl.post(
                f"{_GITHUB_API}/repos/{owner}/{repo}/issues",
                json={"title": title, "body": body},
                headers=_headers(),
            )
            r.raise_for_status()
            d = r.json()
            return {"number": d.get("number"), "url": d.get("html_url"), "state": d.get("state"), "error": None}
    except Exception as e:
        return {"error": str(e)}
