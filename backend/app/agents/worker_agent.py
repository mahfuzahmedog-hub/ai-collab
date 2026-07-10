import asyncio
import json
import logging
import re
from typing import Optional
from app.agents.base_agent import BaseAgent
from app.models.agent import Agent, AgentStatus
from app.models.task import Task, TaskStatus
from app.core.event_bus import event_bus
from app.workspace.manager import write_file, read_file, list_files
from app.db.repository import load_project_messages

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

    def _parse_actions(self, text: str) -> list[dict]:
        matches = re.findall(r'\[ACTION\](.*?)\[/ACTION\]', text, re.DOTALL)
        actions = []
        for m in matches:
            try:
                actions.append(json.loads(m.strip()))
            except json.JSONDecodeError:
                logger.warning("WorkerAgent %s: failed to parse action: %s", self.name, m[:120])
        return actions

    async def _execute_action(self, action: dict) -> str:
        t = action.get("type")
        if t == "write_file":
            path = action.get("path", "")
            content = action.get("content", "")
            if path:
                result = await write_file(self.agent.project_id, path, content)
                return f"Created {path} ({result['size']} bytes)"
        elif t == "read_file":
            path = action.get("path", "")
            if path:
                try:
                    content = await read_file(self.agent.project_id, path)
                    return f"Read {path}: {content[:200]}..."
                except FileNotFoundError:
                    return f"File not found: {path}"
        elif t == "list_files":
            files = await list_files(self.agent.project_id)
            return f"Files: {', '.join(f['path'] for f in files)}"
        return ""

    async def work_on_task(self) -> str:
        if not self.current_task:
            return "No task assigned."

        self.current_task.status = TaskStatus.working
        await self.send_message(
            self.agent.project_id,
            f"Starting work on '{self.current_task.title}'...",
            msg_type="task_update",
            channel="general",
        )

        # Inject recent group chat context
        recent = await load_project_messages(self.agent.project_id, limit=15)
        context = ""
        if recent:
            context = "\nRecent team chat:\n" + "\n".join(
                f"[{m.sender_name}]: {m.content[:200]}" for m in recent[-10:]
            )

        prompt = f"""You are working on the following task:

Title: {self.current_task.title}
Description: {self.current_task.description}
Priority: {self.current_task.priority.value}
{context}

Please work on this task now. Think through the approach, implement the solution, and describe what you're doing. When you write files, use [ACTION] blocks. Be thorough and detailed."""

        result = await self.think(prompt)

        # Parse and execute any file actions
        actions = self._parse_actions(result)
        for action in actions:
            feedback = await self._execute_action(action)
            if feedback:
                await self.send_message(
                    self.agent.project_id,
                    feedback,
                    msg_type="file",
                    channel="general",
                )

        # Strip action blocks from displayed response
        clean_result = re.sub(r'\[ACTION\].*?\[/ACTION\]', '', result, flags=re.DOTALL).strip()

        self.current_task.status = TaskStatus.completed
        self.completed_tasks.append(self.current_task)
        self.agent.memory["completed_tasks"].append({
            "task_id": self.current_task.id,
            "title": self.current_task.title,
            "result": clean_result[:500],
        })

        await self.send_message(
            self.agent.project_id,
            f"Completed task '{self.current_task.title}'.\n\n{clean_result[:300]}",
            msg_type="task_complete",
            channel="general",
            metadata={"task_id": self.current_task.id},
        )

        old_task = self.current_task
        self.current_task = None
        self.agent.current_task_id = None
        self.status = AgentStatus.idle

        return clean_result

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

As a {self.agent.role} with skills in {', '.join(self.agent.skills)}, please provide helpful assistance."""

        return await self.think(prompt)

    async def report_blocker(self, issue: str):
        await self.send_message(
            self.agent.project_id,
            f"Blocked: {issue}\nI need help resolving this.",
            msg_type="task_update",
            channel="general",
        )
        self.status = AgentStatus.blocked

    async def handle_direct_message(self, project_id: str, user_message: str):
        prompt = f"""The user has sent you a direct message:
{user_message}

You are {self.name}, a {self.agent.role} with skills in {', '.join(self.agent.skills)}.
Respond helpfully and professionally. You can offer to take on tasks, answer questions, or provide information."""
        response = await self.think(prompt)
        clean = re.sub(r'\[ACTION\].*?\[/ACTION\]', '', response, flags=re.DOTALL).strip()
        dm_channel = f"dm-{self.name.lower().replace(' ', '-')}"
        await self.send_message(project_id, clean, channel=dm_channel)