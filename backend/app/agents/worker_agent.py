from __future__ import annotations
import asyncio
import json
import logging
import re
from typing import Any, Optional
from app.agents.base_agent import BaseAgent
from app.models.agent import Agent, AgentStatus
from app.models.task import Task, TaskStatus
from app.core.event_bus import event_bus
from app.workspace.manager import write_file, read_file, list_files
from app.db.repository import load_project_messages
from app.tools.registry import tool_registry
from app.graph.engine import GraphEngine, START, END
from app.graph.types import Command

logger = logging.getLogger(__name__)

_WORKER_SYSTEM_TOOLS = {"write_file", "read_file", "list_files"}


class WorkerAgent(BaseAgent):
    def __init__(self, agent: Agent):
        super().__init__(agent)
        self.current_task: Optional[Task] = None
        self.completed_tasks: list[Task] = []

    def assign_task(self, task: Task):
        self.current_task = task
        self.agent.current_task_id = task.id
        asyncio.create_task(self.set_status(AgentStatus.assigned, f"Assigned task: {task.title}"))
        asyncio.create_task(self.set_status(AgentStatus.working, f"Working on task: {task.title}"))

    async def execute_tool(self, tool_name: str, params: dict) -> str:
        if tool_name == "write_file":
            path = params.get("path", "")
            content = params.get("content", "")
            if path:
                result = await write_file(self.agent.project_id, path, content)
                return f"Created {path} ({result['size']} bytes)"
            return "No path provided."
        elif tool_name == "read_file":
            path = params.get("path", "")
            if path:
                try:
                    content = await read_file(self.agent.project_id, path)
                    return f"Read {path}: {content[:500]}"
                except FileNotFoundError:
                    return f"File not found: {path}"
            return "No path provided."
        elif tool_name == "list_files":
            files = await list_files(self.agent.project_id)
            return "\n".join(f"{f['path']} ({f['size']} bytes)" for f in files)
        return await super().execute_tool(tool_name, params)

    def _build_worker_graph(self) -> GraphEngine:
        builder = GraphEngine()
        builder.set_entry_point("plan_node")

        async def plan_node(state: dict) -> Command:
            task = state.get("task", {})
            context = state.get("context", "")
            plan_prompt = f"""Analyze this task and create a plan:

Title: {task.get('title', '')}
Description: {task.get('description', '')}
Priority: {task.get('priority', 'medium')}
{context}

Create a step-by-step plan to complete this task. List the files you need to create or modify."""
            state["_plan"] = plan_prompt
            return Command(goto="execute_node")

        async def execute_node(state: dict) -> Command:
            plan = state.get("_plan", "")
            context = state.get("context", "")
            task = state.get("task", {})
            prompt = f"""You are working on the following task:

Title: {task.get('title', '')}
Description: {task.get('description', '')}
Priority: {task.get('priority', 'medium')}
{context}

Plan: {plan[:500]}

Please work on this task now. Think through the approach, implement the solution, and describe what you're doing. Use write_file tool when you write code files. Be thorough and detailed."""
            state["_execute_prompt"] = prompt
            builder = self._build_agent_graph()
            graph = builder.compile()
            graph_state: dict[str, Any] = {
                "messages": self._build_messages(prompt),
                "temperature": self.agent.temperature,
                "provider": self.agent.provider,
                "project_id": self.agent.project_id,
                "agent_id": self.id,
                "response": "",
                "_tool_calls": [],
                "_has_tool_calls": False,
                "_new_content": "",
                "_tool_results": [],
            }
            recall = await self._enrich_with_memories(prompt)
            if recall:
                graph_state["messages"][0]["content"] += recall
            skills_block = await self._enrich_with_skills(prompt)
            if skills_block:
                graph_state["messages"][0]["content"] += skills_block
            result = ""
            async for snapshot in graph.stream(graph_state):
                new_content = snapshot.get("_new_content", "")
                if new_content:
                    result += new_content
            state["_result"] = result.strip()
            return Command(goto="review_node")

        async def review_node(state: dict) -> Command:
            result = state.get("_result", "")
            review_prompt = f"""Review this completed work:

Title: {state.get('task', {}).get('title', '')}
Result: {result[:1000]}

Evaluate quality, completeness, and potential issues. Score 1-10."""
            review = await self.think(review_prompt)
            state["_review"] = review
            return Command()

        builder.add_node("plan_node", plan_node)
        builder.add_node("execute_node", execute_node)
        builder.add_node("review_node", review_node)
        builder.add_edge("plan_node", "execute_node")
        builder.add_edge("execute_node", "review_node")
        builder.set_finish_point("review_node")
        return builder

    async def work_on_task(self) -> str:
        if not self.current_task:
            return "No task assigned."
        self.current_task.status = TaskStatus.working
        from app.db.repository import update_task_fields
        await update_task_fields(self.agent.project_id, self.current_task.id, status="working")
        await self.send_message(
            self.agent.project_id,
            f"Starting work on '{self.current_task.title}'...",
            msg_type="task_update", channel=self.agent.channel,
        )
        recent = await load_project_messages(self.agent.project_id, limit=15)
        context = ""
        if recent:
            context = "\nRecent team chat:\n" + "\n".join(
                f"[{m.sender_name}]: {m.content[:200]}" for m in recent[-10:]
            )
        state: dict[str, Any] = {
            "task": {
                "title": self.current_task.title,
                "description": self.current_task.description,
                "priority": self.current_task.priority.value,
            },
            "context": context,
            "_plan": "",
            "_result": "",
            "_review": "",
        }
        graph = self._build_worker_graph().compile()
        async for snapshot in graph.stream(state):
            pass
        clean_result = state.get("_result", "")
        self.current_task.status = TaskStatus.completed
        await update_task_fields(self.agent.project_id, self.current_task.id, status="completed")
        self.completed_tasks.append(self.current_task)
        self.agent.memory["completed_tasks"].append({
            "task_id": self.current_task.id,
            "title": self.current_task.title,
            "result": clean_result[:500],
        })
        await self.send_message(
            self.agent.project_id,
            f"Completed task '{self.current_task.title}'.\n\n{clean_result[:300]}",
            msg_type="task_complete", channel=self.agent.channel,
            metadata={"task_id": self.current_task.id},
        )
        old_task = self.current_task
        self.current_task = None
        self.agent.current_task_id = None
        asyncio.create_task(self.set_status(AgentStatus.idle, "Task completed"))
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
            msg_type="task_update", channel=self.agent.channel,
        )
        asyncio.create_task(self.set_status(AgentStatus.blocked, issue))

    async def handle_direct_message(self, project_id: str, user_message: str):
        prompt = f"""The user has sent you a direct message:
{user_message}

You are {self.name}, a {self.agent.role} with skills in {', '.join(self.agent.skills)}.
Respond helpfully and professionally. You can offer to take on tasks, answer questions, or provide information."""
        response = ""
        async for chunk in self.think_with_tools(prompt):
            response += chunk
        clean = response.strip() or "I received your message. How can I help?"
        dm_channel = f"dm-{self.name.lower().replace(' ', '-')}"
        await self.send_message(project_id, clean, channel=dm_channel)
