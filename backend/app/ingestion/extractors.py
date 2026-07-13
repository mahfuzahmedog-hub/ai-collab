from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PDFExtractor:
    async def extract(self, path: str) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text.strip()
        except ImportError:
            logger.warning("pypdf not installed, using fallback")
            return f"[PDF file: {path}]"
        except Exception as e:
            logger.error("PDF extraction failed: %s", e)
            return f"[PDF extraction error: {e}]"


class WebExtractor:
    async def extract(self, url: str) -> str:
        try:
            import trafilatura
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                if text:
                    return text.strip()
            return f"[Web page: {url}]"
        except ImportError:
            try:
                import httpx
                resp = await httpx.get(url, timeout=30, follow_redirects=True)
                resp.raise_for_status()
                import re
                text = re.sub(r'<[^>]+>', ' ', resp.text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:10000]
            except Exception as e:
                logger.error("Web extraction fallback failed: %s", e)
                return f"[Web page: {url}]"
        except Exception as e:
            logger.error("Web extraction failed: %s", e)
            return f"[Web extraction error: {e}]"


class ImageExtractor:
    async def extract(self, path: str) -> str:
        try:
            import pytesseract
            from PIL import Image
            image = Image.open(path)
            text = pytesseract.image_to_string(image)
            return text.strip() or f"[No text detected in image: {path}]"
        except ImportError:
            return f"[Image file: {path}]"
        except Exception as e:
            logger.error("OCR extraction failed: %s", e)
            return f"[OCR error: {e}]"


class AudioExtractor:
    async def extract(self, path: str) -> str:
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(path)
            return result.get("text", "").strip()
        except ImportError:
            return f"[Audio file: {path}]"
        except Exception as e:
            logger.error("Audio transcription failed: %s", e)
            return f"[Transcription error: {e}]"
