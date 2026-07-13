from __future__ import annotations
import asyncio
import base64
import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


class STTEngine:
    def __init__(self):
        self._deepgram_key = ""

    async def transcribe(self, audio_base64: str, model: str = "whisper") -> dict:
        if not audio_base64:
            return {"error": "No audio provided"}
        try:
            import openai
            audio_bytes = base64.b64decode(audio_base64)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                tmp_path = f.name
            client = openai.AsyncOpenAI()
            with open(tmp_path, "rb") as audio_file:
                resp = await client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            os.unlink(tmp_path)
            return {"text": resp.text, "engine": "whisper"}
        except ImportError:
            pass
        except Exception as e:
            logger.warning("Whisper STT failed: %s", e)
        return {"text": "", "engine": "none", "note": "STT requires openai/whisper"}


stt_engine = STTEngine()
