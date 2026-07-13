from __future__ import annotations
import logging
import uuid
from pathlib import Path
from typing import Any, Optional

from app.ingestion.extractors import PDFExtractor, WebExtractor, ImageExtractor, AudioExtractor
from app.ingestion.chunkers import GeneralChunker
from app.memory.blocks import MemoryBlock
from app.memory.memfs import MemFS
from app.llm import llm_router

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(self, memfs: MemFS):
        self.memfs = memfs
        self.extractors = {
            ".pdf": PDFExtractor(),
            ".png": ImageExtractor(), ".jpg": ImageExtractor(), ".jpeg": ImageExtractor(),
            ".gif": ImageExtractor(), ".bmp": ImageExtractor(),
            ".mp3": AudioExtractor(), ".wav": AudioExtractor(), ".m4a": AudioExtractor(),
            ".ogg": AudioExtractor(),
        }
        self.web_extractor = WebExtractor()
        self.chunker = GeneralChunker()

    async def ingest_file(self, path: str, project_id: str, metadata: Optional[dict] = None) -> list[str]:
        p = Path(path)
        ext = p.suffix.lower()
        extractor = self.extractors.get(ext)
        if not extractor:
            logger.warning("No extractor for %s", ext)
            return []
        text = await extractor.extract(path)
        if not text or text.startswith("[") and text.endswith("]"):
            return []
        return await self._process_text(text, project_id, metadata or {})

    async def ingest_url(self, url: str, project_id: str, metadata: Optional[dict] = None) -> list[str]:
        text = await self.web_extractor.extract(url)
        if not text or text.startswith("[") and text.endswith("]"):
            return []
        return await self._process_text(text, project_id, {**(metadata or {}), "source_url": url})

    async def ingest_text(self, text: str, project_id: str, metadata: Optional[dict] = None) -> list[str]:
        return await self._process_text(text, project_id, metadata or {})

    async def _process_text(self, text: str, project_id: str, metadata: dict) -> list[str]:
        chunks = self.chunker.chunk(text)
        block_ids = []
        for chunk in chunks:
            block = MemoryBlock(
                id=f"ingest-{uuid.uuid4().hex[:12]}",
                name=metadata.get("name", chunk["content"][:50]),
                content=chunk["content"],
                tags=metadata.get("tags", ["ingested"]),
                metadata={**metadata, "chunk_index": chunk["index"]},
            )
            block_id = await self.memfs.save_block(block, project_id)
            block_ids.append(block_id)
        await self._generate_embedding_summary(text, project_id, metadata)
        logger.info("Ingested %d chunks for project %s", len(chunks), project_id)
        return block_ids

    async def _generate_embedding_summary(self, text: str, project_id: str, metadata: dict):
        summary_block = MemoryBlock(
            id=f"summary-{uuid.uuid4().hex[:12]}",
            name=f"Summary: {metadata.get('name', text[:50])}",
            content=text[:2000],
            system_flag=True,
            tags=["summary", "ingested"],
            metadata=metadata,
        )
        await self.memfs.save_block(summary_block, project_id)
