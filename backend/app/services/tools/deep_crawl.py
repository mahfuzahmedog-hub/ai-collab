import logging

logger = logging.getLogger(__name__)


async def crawl(url: str, max_pages: int = 10) -> dict:
    try:
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
        from crawl4ai.deep_crawling.strategy import OnPageYielded
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlStrategy

        pages: list[dict] = []
        seen = set()

        async def on_page(page: OnPageYielded):
            if len(pages) >= max_pages:
                return
            if page.url in seen:
                return
            seen.add(page.url)
            pages.append({
                "url": page.url,
                "title": page.metadata.get("title", "") if page.metadata else "",
                "content": page.markdown or "",
            })

        strategy = BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=max_pages,
            on_page_yielded=on_page,
        )

        async with AsyncWebCrawler() as crawler:
            await crawler.arun(url=url, deep_crawl_strategy=strategy)

        return {"urls_crawled": len(pages), "pages": pages}

    except ImportError:
        return {"error": "crawl4ai not installed"}
    except Exception as e:
        logger.error("deep crawl failed: %s", e)
        return {"error": str(e), "urls_crawled": 0, "pages": []}
