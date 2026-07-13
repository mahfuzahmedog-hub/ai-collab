from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class OCREngine:
    async def ocr_image(self, image_path: str) -> dict:
        try:
            import pytesseract
            from PIL import Image
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return {"text": text.strip(), "engine": "tesseract"}
        except ImportError:
            return {"text": "", "engine": "none", "note": "pytesseract required"}
        except Exception as e:
            logger.warning("OCR failed: %s", e)
            return {"text": "", "engine": "error", "error": str(e)}

    async def understand_screenshot(self, image_path: str, prompt: str = "Describe this image") -> dict:
        from app.llm import llm_router
        import base64
        try:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            provider = llm_router.get_provider("omniroute")
            if provider and hasattr(provider, "_client"):
                resp = await provider._client.post(
                    f"{provider.config.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {provider._next_key()}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "user", "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                            ]}
                        ],
                    }, timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {"description": content, "engine": "vision"}
        except Exception as e:
            logger.warning("Screenshot understanding failed: %s", e)
            return {"description": "", "engine": "error", "error": str(e)}
        return {"description": "", "engine": "none"}


ocr_engine = OCREngine()
