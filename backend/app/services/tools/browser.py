import asyncio
import logging

logger = logging.getLogger(__name__)

_playwright_available = None
_playwright = None


def _ensure_playwright():
    global _playwright_available, _playwright
    if _playwright_available is not None:
        return _playwright_available
    try:
        import playwright
        _playwright = playwright
        _playwright_available = True
    except ImportError:
        _playwright_available = False
    return _playwright_available


async def browse(url: str, timeout: int = 30000) -> dict:
    if not _ensure_playwright():
        return {"title": "", "content": "", "url": url, "error": "playwright not installed — run `pip install playwright && playwright install chromium`"}
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            title = await page.title()
            text = await page.evaluate("document.body?.innerText || ''")
            content = text[:5000]
            final_url = page.url
            await browser.close()
            return {"title": title, "content": content, "url": final_url, "error": None}
    except Exception as e:
        logger.exception("browse failed")
        return {"title": "", "content": "", "url": url, "error": str(e)}


async def screenshot(url: str, timeout: int = 30000) -> dict:
    if not _ensure_playwright():
        return {"screenshot_base64": "", "url": url, "error": "playwright not installed — run `pip install playwright && playwright install chromium`"}
    try:
        from playwright.async_api import async_playwright
        import base64
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            png = await page.screenshot(full_page=False)
            b64 = base64.b64encode(png).decode("utf-8")
            await browser.close()
            return {"screenshot_base64": b64, "url": url, "error": None}
    except Exception as e:
        logger.exception("screenshot failed")
        return {"screenshot_base64": "", "url": url, "error": str(e)}
