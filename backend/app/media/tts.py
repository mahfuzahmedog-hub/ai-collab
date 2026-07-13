from __future__ import annotations
import asyncio
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TTSEngine:
    def __init__(self):
        self._eleven_api_key = ""

    async def synthesize(self, text: str, voice: str = "default") -> dict:
        if not text:
            return {"error": "No text provided"}
        try:
            from elevenlabs import generate, Voice, save
            if self._eleven_api_key:
                audio = generate(text=text, voice=voice, api_key=self._eleven_api_key)
                b64 = base64.b64encode(audio).decode("utf-8")
                return {"audio_base64": b64, "format": "mp3", "engine": "elevenlabs"}
        except ImportError:
            pass
        return await self._system_tts(text)

    async def _system_tts(self, text: str) -> dict:
        import platform
        system = platform.system()
        try:
            if system == "Darwin":
                proc = await asyncio.create_subprocess_exec("say", text, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await proc.wait()
                return {"audio_base64": "", "format": "system", "engine": "macos_say"}
            elif system == "Linux":
                proc = await asyncio.create_subprocess_exec("espeak", text, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await proc.wait()
                return {"audio_base64": "", "format": "system", "engine": "espeak"}
        except Exception as e:
            logger.warning("System TTS failed: %s", e)
        return {"audio_base64": "", "format": "none", "engine": "none"}


tts_engine = TTSEngine()
