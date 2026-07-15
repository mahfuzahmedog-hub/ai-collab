from __future__ import annotations
import asyncio
import base64
import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

_playwright_available = None


def _ensure_playwright():
    global _playwright_available
    if _playwright_available is not None:
        return _playwright_available
    try:
        import playwright
        _playwright_available = True
    except ImportError:
        _playwright_available = False
    return _playwright_available


class BrowserManager:
    def __init__(self):
        self._browser = None
        self._context = None
        self._pages: dict[str, Any] = {}
        self._current_page_id: Optional[str] = None

    async def _ensure_browser(self):
        if self._browser:
            return
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().__aenter__()
        self._browser = await self._pw.chromium.launch(headless=True)
        self._context = await self._browser.new_context()

    async def new_page(self, url: str = "") -> dict:
        await self._ensure_browser()
        page = await self._context.new_page()
        page_id = f"tab-{len(self._pages) + 1}"
        self._pages[page_id] = page
        self._current_page_id = page_id
        if url:
            await page.goto(url, wait_until="domcontentloaded")
        return {"page_id": page_id, "url": url}

    async def navigate(self, url: str, page_id: Optional[str] = None) -> dict:
        page = self._get_page(page_id)
        if not page:
            return {"error": "No browser page open"}
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        return {"url": page.url, "title": await page.title()}

    async def click(self, selector: str, page_id: Optional[str] = None) -> dict:
        page = self._get_page(page_id)
        if not page:
            return {"error": "No browser page open"}
        try:
            await page.click(selector, timeout=5000)
            return {"success": True, "url": page.url}
        except Exception as e:
            return {"error": str(e)}

    async def type_text(self, selector: str, text: str, page_id: Optional[str] = None) -> dict:
        page = self._get_page(page_id)
        if not page:
            return {"error": "No browser page open"}
        try:
            await page.fill(selector, text)
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def scroll(self, delta_x: int = 0, delta_y: int = 500, page_id: Optional[str] = None) -> dict:
        page = self._get_page(page_id)
        if not page:
            return {"error": "No browser page open"}
        await page.evaluate(f"window.scrollBy({delta_x}, {delta_y})")
        return {"success": True}

    async def extract_text(self, selector: Optional[str] = None, page_id: Optional[str] = None) -> dict:
        page = self._get_page(page_id)
        if not page:
            return {"error": "No browser page open"}
        if selector:
            elements = await page.query_selector_all(selector)
            texts = [await el.inner_text() for el in elements]
            return {"texts": texts, "count": len(texts)}
        text = await page.evaluate("document.body?.innerText || ''")
        return {"text": text[:10000], "url": page.url, "title": await page.title()}

    async def screenshot(self, page_id: Optional[str] = None) -> dict:
        page = self._get_page(page_id)
        if not page:
            return {"error": "No browser page open"}
        png = await page.screenshot(full_page=False)
        b64 = base64.b64encode(png).decode("utf-8")
        return {"screenshot_base64": b64, "url": page.url}

    async def list_tabs(self) -> list[dict]:
        return [{"page_id": pid, "url": p.url, "title": await p.title()} for pid, p in self._pages.items()]

    async def switch_tab(self, page_id: str) -> dict:
        if page_id in self._pages:
            self._current_page_id = page_id
            page = self._pages[page_id]
            return {"page_id": page_id, "url": page.url, "title": await page.title()}
        return {"error": f"Tab {page_id} not found"}

    async def close_tab(self, page_id: Optional[str] = None) -> dict:
        pid = page_id or self._current_page_id
        if pid and pid in self._pages:
            await self._pages[pid].close()
            del self._pages[pid]
            if self._current_page_id == pid:
                self._current_page_id = next(iter(self._pages.keys()), None)
            return {"closed": pid}
        return {"error": "No tab to close"}

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None

    def _get_page(self, page_id: Optional[str] = None):
        pid = page_id or self._current_page_id
        return self._pages.get(pid)


_browser_manager = BrowserManager()


async def browse(url: str, timeout: int = 30000) -> dict:
    try:
        from crawl4ai import AsyncWebCrawler
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            return {
                "title": result.metadata.get("title", "") if result.metadata else "",
                "content": result.markdown or "",
                "url": result.url or url,
            }
    except Exception as e:
        logger.warning("crawl4ai browse failed (%s), falling back to playwright", e)
        if not _ensure_playwright():
            return {"error": "crawl4ai and playwright both unavailable"}
        result = await _browser_manager.new_page(url)
        if result.get("page_id"):
            info = await _browser_manager.extract_text()
            return {"title": info.get("title", ""), "content": info.get("text", ""), "url": info.get("url", url)}
        return result


async def screenshot(url: str, timeout: int = 30000) -> dict:
    if not _ensure_playwright():
        return {"error": "playwright not installed"}
    await _browser_manager.new_page(url)
    return await _browser_manager.screenshot()


async def browser_navigate(url: str) -> dict:
    return await _browser_manager.navigate(url)


async def browser_click(selector: str) -> dict:
    return await _browser_manager.click(selector)


async def browser_type(selector: str, text: str) -> dict:
    return await _browser_manager.type_text(selector, text)


async def browser_scroll(delta_y: int = 500) -> dict:
    return await _browser_manager.scroll(delta_y=delta_y)


async def browser_extract(selector: Optional[str] = None) -> dict:
    return await _browser_manager.extract_text(selector)


async def browser_screenshot() -> dict:
    return await _browser_manager.screenshot()


async def browser_list_tabs() -> list[dict]:
    return await _browser_manager.list_tabs()


async def browser_switch_tab(page_id: str) -> dict:
    return await _browser_manager.switch_tab(page_id)
