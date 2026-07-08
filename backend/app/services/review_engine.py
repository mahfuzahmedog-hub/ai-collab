import logging
from datetime import datetime
from app.models.task import Task, TaskStatus
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)


class ReviewEngine:
    async def submit_for_review(self, task: Task, reviewer_id: str):
        task.status = TaskStatus.review
        task.reviews.append({
            "reviewer_id": reviewer_id,
            "status": "pending",
            "submitted_at": datetime.utcnow().isoformat(),
        })
        await event_bus.publish("review_requested", {
            "task_id": task.id,
            "task_title": task.title,
            "reviewer_id": reviewer_id,
        })

    async def approve(self, task: Task, reviewer_id: str, comments: str = ""):
        task.reviews.append({
            "reviewer_id": reviewer_id,
            "status": "approved",
            "comments": comments,
            "timestamp": datetime.utcnow().isoformat(),
        })
        task.status = TaskStatus.testing
        await event_bus.publish("review_approved", {
            "task_id": task.id,
            "task_title": task.title,
            "reviewer_id": reviewer_id,
            "comments": comments,
        })

    async def reject(self, task: Task, reviewer_id: str, reason: str):
        task.reviews.append({
            "reviewer_id": reviewer_id,
            "status": "rejected",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        task.status = TaskStatus.revision
        await event_bus.publish("review_rejected", {
            "task_id": task.id,
            "task_title": task.title,
            "reviewer_id": reviewer_id,
            "reason": reason,
        })


review_engine = ReviewEngine()
