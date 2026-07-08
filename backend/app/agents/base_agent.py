import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, AsyncGenerator
from app.models.agent import Agent, AgentStatus
from app.models.message import Message
from app.llm import llm_router
from app.core.event_bus import event_bus

logger = logging.getLogger(__name__)


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
        self.agent.last_active = datetime.utcnow()

    async def think(self, prompt: str, temperature: Optional[float] = None) -> str:
        self.status = AgentStatus.thinking
        messages = [
            {"role": "system", "content": self._system_prompt()},
            *self.agent.chat_history[-20:],
            {"role": "user", "content": prompt},
        ]
        try:
            response = await llm_router.chat(
                messages,
                provider=self.agent.provider,
                temperature=temperature or self.agent.temperature,
            )
        except Exception as e:
            logger.error("Agent %s think error: %s", self.name, e)
            response = f"I received your request but the LLM service is currently unavailable. Please ensure the configured provider ({self.agent.provider}) is running and accessible."
        self.agent.chat_history.append({"role": "user", "content": prompt})
        self.agent.chat_history.append({"role": "assistant", "content": response})
        self.agent.memory["short_term"].append({"prompt": prompt, "response": response})
        self.status = AgentStatus.idle
        return response

    async def think_stream(self, prompt: str, temperature: Optional[float] = None) -> AsyncGenerator[str, None]:
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
                yield chunk
            self.agent.chat_history.append({"role": "user", "content": prompt})
            self.agent.chat_history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            logger.error("Agent %s stream error: %s", self.name, e)
            yield f"[Error: {e}]"
        self.status = AgentStatus.idle

    async def send_message(self, project_id: str, content: str, msg_type: str = "chat", mentions: Optional[list[str]] = None):
        msg = Message(
            project_id=project_id,
            sender_id=self.id,
            sender_name=self.name,
            sender_role=self.agent.role.value if hasattr(self.agent.role, 'value') else str(self.agent.role),
            content=content,
            msg_type=msg_type,
            mentions=mentions or [],
        )
        await event_bus.publish("message", msg.model_dump())
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
            "You can ask questions, suggest ideas, report progress, request reviews, and help others."
        )
