import asyncio
import logging
from typing import Optional
from app.agents.base_agent import BaseAgent
from app.models.agent import Agent, AgentStatus
from app.models.task import Task, TaskStatus
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)


class WorkerAgent(BaseAgent):
    def __init__(self, agent: Agent):
        super().__init__(agent)
        self.current_task: Optional[Task] = None
        self.completed_tasks: list[Task] = []

    def assign_task(self, task: Task):
        self.current_task = task
        self.agent.current_task_id = task.id
        self.status = AgentStatus.working

    async def work_on_task(self) -> str:
        if not self.current_task:
            return "No task assigned."

        self.current_task.status = TaskStatus.working
        await self.send_message(
            self.agent.project_id,
            f"🔨 Starting work on '{self.current_task.title}'...",
            msg_type="task_update",
        )

        prompt = f"""You are working on the following task:

Title: {self.current_task.title}
Description: {self.current_task.description}
Priority: {self.current_task.priority.value}

Please work on this task now. Think through the approach, implement the solution, and describe what you're doing. Be thorough and detailed."""

        result = await self.think(prompt)

        self.current_task.status = TaskStatus.completed
        self.completed_tasks.append(self.current_task)
        self.agent.memory["completed_tasks"].append({
            "task_id": self.current_task.id,
            "title": self.current_task.title,
            "result": result[:500],
        })

        await self.send_message(
            self.agent.project_id,
            f"✅ Completed task '{self.current_task.title}'.\n\nSummary: {result[:300]}...",
            msg_type="task_complete",
            metadata={"task_id": self.current_task.id},
        )

        old_task = self.current_task
        self.current_task = None
        self.agent.current_task_id = None
        self.status = AgentStatus.idle

        return result

    async def review_work(self, work_description: str) -> dict:
        prompt = f"""Please review the following work:

{work_description}

Evaluate:
1. Quality and completeness
2. Potential issues or bugs
3. Suggestions for improvement
4. Security concerns
5. Overall score (1-10)

Provide a thorough review."""

        review_text = await self.think(prompt)
        return {"reviewer": self.name, "review": review_text, "approved": "good" in review_text.lower()[:200]}

    async def help_teammate(self, question: str) -> str:
        prompt = f"""A teammate needs your help with the following:

{question}

As a {self.agent.role.value} with skills in {', '.join(self.agent.skills)}, please provide helpful assistance."""

        return await self.think(prompt)

    async def report_blocker(self, issue: str):
        await self.send_message(
            self.agent.project_id,
            f"🚧 Blocked: {issue}\nI need help resolving this.",
            msg_type="task_update",
        )
        self.status = AgentStatus.blocked
