from __future__ import annotations
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class CronScheduler:
    def __init__(self):
        self._jobs: dict[str, dict] = {}
        self._running = False

    def add_job(self, job_id: str, schedule: dict, callback: Callable[[dict], Any]):
        self._jobs[job_id] = {"schedule": schedule, "callback": callback, "last_run": None}
        logger.info("Scheduled job %s: %s", job_id, schedule)

    def remove_job(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None

    def _should_run(self, job: dict) -> bool:
        sched = job["schedule"]
        now = datetime.utcnow()
        minute = sched.get("minute")
        hour = sched.get("hour")
        day = sched.get("day")
        if minute is not None and now.minute != int(minute):
            return False
        if hour is not None and now.hour != int(hour):
            return False
        if day is not None and now.day != int(day):
            return False
        return True

    async def start(self):
        self._running = True
        while self._running:
            now = datetime.utcnow()
            for job_id, job in list(self._jobs.items()):
                if self._should_run(job) and (not job["last_run"] or (now - job["last_run"]).total_seconds() > 60):
                    job["last_run"] = now
                    try:
                        await job["callback"](job["schedule"])
                    except Exception as e:
                        logger.error("Cron job %s failed: %s", job_id, e)
            await asyncio.sleep(30)

    async def stop(self):
        self._running = False


cron_scheduler = CronScheduler()
