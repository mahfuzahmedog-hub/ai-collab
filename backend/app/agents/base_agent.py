import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Optional, AsyncGenerator, List, Dict, Any
from app.models.agent import Agent, AgentStatus
from app.models.message import Message
from app.llm import llm_router
from app.core.event_bus import event_bus
from app.db.repository import save_agent, save_message
from app.workspace.manager import write_file, read_file, list_files, get_file_tree

logger = logging.getLogger(__name__)


ACTION_PATTERN = re.compile(r'\[ACTION\](.*?)\[/ACTION\]', re.DOTALL)

class BaseAgent:
    def __init__(self, agent: Agent):
        self.agent = agent
        self._running = False
        self._task: Optional[asyncio.Task] = None

    @property
    def id(self) -> str:
        return self.agent.id

    @property
    def name(self) -> str:
        return self.agent.name

    @property
    def role(self):
        return self.agent.role

    @property
    def status(self) -> AgentStatus:
        return self.agent.status

    @status.setter
    def status(self, value: AgentStatus):
        self.agent.status = value
        self.agent.last_active = datetime.utcnow().isoformat() + "Z"

    def _parse_actions(self, text: str) -> List[Dict[str, Any]]:
        actions = []
        for match in ACTION_PATTERN.finditer(text):
            try:
                actions.append(json.loads(match.group(1).strip()))
            except json.JSONDecodeError:
                logger.warning("Failed to parse action: %s", match.group(1)[:100])
        return actions

    async def _execute_file_action(self, action: Dict[str, Any], project_id: str) -> Optional[str]:
        atype = action.get("type")
        if atype == "write_file":
            result = await write_file(project_id, action["path"], action["content"])
            return f"Created {action['path']} ({result['size']} bytes)"
        elif atype == "read_file":
            content = await read_file(project_id, action["path"])
            return content
        elif atype == "list_files":
            files = await list_files(project_id)
            return "\n".join(f"{f['path']} ({f['size']} bytes)" for f in files)
        return None

    async def think(self, prompt: str, temperature: Optional[float] = None) -> str:
        self.status = AgentStatus.thinking
        memory_block = ""
        if self.agent.memory.get("facts"):
            memory_block = "\nMemory:\n" + "\n".join(
                f"- {k}: {v}" for k, v in self.agent.memory["facts"].items()
            )
        messages = [
            {"role": "system", "content": self._system_prompt() + memory_block},
            *self.agent.chat_history[-100:],
            {"role": "user", "content": prompt},
        ]
        try:
            provider = llm_router.get_provider(self.agent.provider)
            if not provider:
                raise RuntimeError("No LLM provider configured")
            response = await provider.chat(
                messages,
                temperature=temperature or self.agent.temperature,
            )
            if response.startswith("["):
                raise RuntimeError(f"Provider error: {response}")
        except Exception as e:
            logger.error("Agent %s think error: %s", self.name, e)
            response = f"I received your request but the LLM service is currently unavailable. Please ensure the configured provider ({self.agent.provider}) is running and accessible."
        self.agent.chat_history.append({"role": "user", "content": prompt})
        self.agent.chat_history.append({"role": "assistant", "content": response})
        self.agent.memory["short_term"].append({"prompt": prompt, "response": response})
        self.status = AgentStatus.idle
        asyncio.create_task(save_agent(self.agent))
        return response

    async def think_stream(self, prompt: str, temperature: Optional[float] = None):
        self.status = AgentStatus.thinking
        messages = [
            {"role": "system", "content": self._system_prompt()},
            *self.agent.chat_history[-20:],
            {"role": "user", "content": prompt},
        ]
        full_response = ""
        try:
            async for chunk in llm_router.chat_stream(
                messages,
                provider=self.agent.provider,
                temperature=temperature or self.agent.temperature,
            ):
                full_response += chunk
                await event_bus.publish("stream_chunk", {
                    "agent_id": self.id,
                    "agent_name": self.name,
                    "agent_role": str(self.role),
                    "project_id": self.agent.project_id,
                    "content": chunk,
                    "done": False,
                })
                yield chunk
            self.agent.chat_history.append({"role": "user", "content": prompt})
            self.agent.chat_history.append({"role": "assistant", "content": full_response})
            await event_bus.publish("stream_chunk", {
                "agent_id": self.id,
                "agent_name": self.name,
                "agent_role": str(self.role),
                "project_id": self.agent.project_id,
                "content": "",
                "done": True,
            })
        except Exception as e:
            logger.error("Agent %s stream error: %s", self.name, e)
            yield f"[Error: {e}]"
            await event_bus.publish("stream_chunk", {
                "agent_id": self.id,
                "agent_name": self.name,
                "agent_role": str(self.role),
                "project_id": self.agent.project_id,
                "content": f"[Error: {e}]",
                "done": True,
            })
        self.status = AgentStatus.idle

    async def send_message(self, project_id: str, content: str, msg_type: str = "chat", mentions: Optional[list[str]] = None, channel: str = "general"):
        msg = Message(
            project_id=project_id,
            sender_id=self.id,
            sender_name=self.name,
            sender_role=self.agent.role.value if hasattr(self.agent.role, 'value') else str(self.agent.role),
            content=content,
            msg_type=msg_type,
            mentions=mentions or [],
            channel=channel,
        )
        await event_bus.publish("message", msg.model_dump())
        asyncio.create_task(save_message(msg))
        return msg

    async def run(self):
        self._running = True
        while self._running:
            await asyncio.sleep(1)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        self.status = AgentStatus.idle

    def _system_prompt(self) -> str:
        return (
            f"You are {self.name}, a {self.agent.role.value} in an AI collaboration team.\n"
            f"Personality: {self.agent.personality}\n"
            f"Skills: {', '.join(self.agent.skills)}\n"
            f"You are working on project {self.agent.project_id}.\n"
            "You communicate naturally with your teammates like a human coworker.\n"
            "Be concise, professional, and collaborative.\n"
            "You can ask questions, suggest ideas, report progress, request reviews, and help others.\n"
            "When writing files, use [ACTION] blocks: [ACTION]{\"type\":\"write_file\",\"path\":\"...\",\"content\":\"...\"}[/ACTION]"
        )
