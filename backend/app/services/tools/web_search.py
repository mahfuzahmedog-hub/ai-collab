import logging
import re
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

_LITE_URL = "https://lite.duckduckgo.com/lite/"


async def search(query: str, num_results: int = 5) -> list[dict]:
    try:
        return await _search_lite(query, num_results)
    except Exception as e1:
        logger.debug("DuckDuckGo Lite failed: %s", e1)
        try:
            return await _search_html(query, num_results)
        except Exception as e2:
            return [{"error": f"All search backends failed: {e2}"}]


def _parse_lite(html: str, limit: int) -> list[dict]:
    results = []
    for tr in re.finditer(r'<tr[^>]*class="result"[^>]*>(.*?)</tr>', html, re.DOTALL):
        link = re.search(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', tr.group(1))
        snippet = re.search(r'<td[^>]*class="result-snippet"[^>]*>(.*?)</td>', tr.group(1), re.DOTALL)
        if link:
            results.append({
                "title": re.sub(r'<[^>]+>', '', link.group(2)).strip(),
                "url": link.group(1),
                "snippet": re.sub(r'<[^>]+>', '', snippet.group(1)).strip() if snippet else "",
            })
        if len(results) >= limit:
            break
    return results


async def _search_lite(query: str, num_results: int) -> list[dict]:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as cl:
        r = await cl.post(_LITE_URL, data={"q": query})
        r.raise_for_status()
        return _parse_lite(r.text, num_results)


async def _search_html(query: str, num_results: int) -> list[dict]:
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as cl:
        r = await cl.get(url)
        r.raise_for_status()
        results = []
        for div in re.finditer(r'<div[^>]*class="result[^"]*"[^>]*>(.*?)</div>\s*</div>', r.text, re.DOTALL):
            link = re.search(r'<a[^>]*href="([^"]*)"[^>]*class="result__a"[^>]*>(.*?)</a>', div.group(1), re.DOTALL)
            snippet = re.search(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', div.group(1), re.DOTALL)
            if link:
                results.append({
                    "title": re.sub(r'<[^>]+>', '', link.group(2)).strip(),
                    "url": link.group(1),
                    "snippet": re.sub(r'<[^>]+>', '', snippet.group(1)).strip() if snippet else "",
                })
            if len(results) >= num_results:
                break
        return results
