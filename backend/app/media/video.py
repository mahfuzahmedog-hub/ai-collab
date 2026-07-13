from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class VideoEngine:
    async def extract_frames(self, video_path: str, interval_seconds: int = 5) -> list[str]:
        frames = []
        try:
            import cv2
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_interval = int(fps * interval_seconds)
            count = 0
            saved = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                if count % frame_interval == 0:
                    path = f"/tmp/frame_{saved}.jpg"
                    cv2.imwrite(path, frame)
                    frames.append(path)
                    saved += 1
                count += 1
            cap.release()
        except ImportError:
            logger.warning("cv2 not installed; cannot extract frames")
        except Exception as e:
            logger.warning("Frame extraction failed: %s", e)
        return frames

    async def analyze(self, video_path: str, prompt: str = "Describe this video") -> dict:
        frames = await self.extract_frames(video_path)
        if not frames:
            return {"description": "", "engine": "none", "note": "cv2 required"}
        from app.media.ocr import ocr_engine
        descriptions = []
        for f in frames[:10]:
            result = await ocr_engine.understand_screenshot(f, prompt)
            if result.get("description"):
                descriptions.append(result["description"])
        summary = "\n".join(descriptions)
        return {"description": summary, "frame_count": len(frames), "engine": "vision"}


video_engine = VideoEngine()
