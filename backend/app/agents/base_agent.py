import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Optional, AsyncGenerator, List, Dict, Any
from app.models.agent import Agent, AgentStatus
from app.services.lifecycle import LifecycleEngine
from app.models.message import Message
from app.models.ops import ExecutionLog
from app.llm import llm_router
from app.core.event_bus import event_bus
from app.db.repository import save_agent, save_message, save_execution_log, load_memories, search_memories
from app.workspace.manager import write_file, read_file, list_files, get_file_tree

logger = logging.getLogger(__name__)


ACTION_PATTERN = re.compile(r'\[ACTION\](.*?)\[/ACTION\]', re.DOTALL)

_TOOL_REGISTRY = {
    "browse": lambda: __import__("app.services.tools.browser", fromlist=["browse"]).browse,
    "screenshot": lambda: __import__("app.services.tools.browser", fromlist=["screenshot"]).screenshot,
    "run_python": lambda: __import__("app.services.tools.code_exec", fromlist=["run_python"]).run_python,
    "run_shell": lambda: __import__("app.services.tools.code_exec", fromlist=["run_shell"]).run_shell,
    "get_repo": lambda: __import__("app.services.tools.github_integration", fromlist=["get_repo"]).get_repo,
    "search_repos": lambda: __import__("app.services.tools.github_integration", fromlist=["search_repos"]).search_repos,
    "get_file_content": lambda: __import__("app.services.tools.github_integration", fromlist=["get_file_content"]).get_file_content,
    "create_issue": lambda: __import__("app.services.tools.github_integration", fromlist=["create_issue"]).create_issue,
    "http_get": lambda: __import__("app.services.tools.api_http", fromlist=["http_get"]).http_get,
    "http_post": lambda: __import__("app.services.tools.api_http", fromlist=["http_post"]).http_post,
    "http_put": lambda: __import__("app.services.tools.api_http", fromlist=["http_put"]).http_put,
    "http_delete": lambda: __import__("app.services.tools.api_http", fromlist=["http_delete"]).http_delete,
    "web_search": lambda: __import__("app.services.tools.web_search", fromlist=["search"]).search,
}

# ponytail: USD per 1K tokens (input, output). Heuristic token counts (~chars/4),
# not exact provider usage; upgrade path is to read real usage from provider responses.
_PRICING = {
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4o": (0.005, 0.015),
    "gpt-4": (0.03, 0.06),
    "claude-3-5-sonnet": (0.003, 0.015),
    "claude-3-haiku": (0.00025, 0.00125),
}


def _estimate_tokens(text: str) -> int:
    return max(1, len(text or "") // 4)


def _estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    rate = None
    for key, r in _PRICING.items():
        if key in (model or ""):
            rate = r
            break
    if not rate:
        return 0.0
    return round((in_tok / 1000) * rate[0] + (out_tok / 1000) * rate[1], 6)

class BaseAgent:
    def __init__(self, agent: Agent):
        self.agent = agent
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lifecycle = LifecycleEngine(agent)

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
    def display_name(self) -> str:
        return self.agent.display_name or self.agent.name

    @property
    def mission(self) -> str:
        return self.agent.mission or ""

    @property
    def status(self) -> AgentStatus:
        return self.agent.status

    @status.setter
    def status(self, value: AgentStatus):
        self.agent.status = value
        self.agent.last_active = datetime.utcnow().isoformat() + "Z"

    async def set_status(self, new_status: AgentStatus, reason: str = "") -> bool:
        return await self._lifecycle.transition_to(new_status, reason)

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

    async def execute_tool(self, tool_name: str, params: dict) -> dict:
        fn = _TOOL_REGISTRY.get(tool_name)
        if not fn:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return await fn()(**params)
        except Exception as e:
            logger.exception("Tool %s failed", tool_name)
            return {"error": str(e)}

    async def think(self, prompt: str, temperature: Optional[float] = None) -> str:
        await self.set_status(AgentStatus.thinking)
        memory_block = ""
        if self.agent.memory.get("facts"):
            memory_block = "\nMemory:\n" + "\n".join(
                f"- {k}: {v}" for k, v in self.agent.memory["facts"].items()
            )
        try:
            memories = await search_memories(self.agent.project_id, prompt, limit=5, agent_id=self.id)
            if not memories:
                memories = await load_memories(self.agent.project_id, self.id, limit=20)
            if memories:
                memory_block += "\nRecall:\n" + "\n".join(
                    f"[{m.type}] {m.content[:200]}" for m in memories
                )
        except Exception:
            pass
        messages = [
            {"role": "system", "content": self._system_prompt() + memory_block},
            *self.agent.chat_history[-100:],
            {"role": "user", "content": prompt},
        ]
        _t0 = time.perf_counter()
        _status = "completed"
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
            _status = "failed"
            response = f"I received your request but the LLM service is currently unavailable. Please ensure the configured provider ({self.agent.provider}) is running and accessible."
        await self._log_execution(prompt, response, _status, int((time.perf_counter() - _t0) * 1000))
        self.agent.chat_history.append({"role": "user", "content": prompt})
        self.agent.chat_history.append({"role": "assistant", "content": response})
        self.agent.memory["short_term"].append({"prompt": prompt, "response": response})
        await self.set_status(AgentStatus.idle)
        return response

    async def think_stream(self, prompt: str, temperature: Optional[float] = None):
        await self.set_status(AgentStatus.thinking)
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
        await self.set_status(AgentStatus.idle)

    async def _log_execution(self, prompt: str, response: str, status: str, latency_ms: int):
        try:
            in_tok = _estimate_tokens(prompt)
            out_tok = _estimate_tokens(response)
            log = ExecutionLog(
                project_id=self.agent.project_id,
                agent_id=self.id,
                agent_name=self.name,
                action="llm_call",
                model=self.agent.model,
                provider=self.agent.provider,
                status=status,
                input_tokens=in_tok,
                output_tokens=out_tok,
                total_tokens=in_tok + out_tok,
                cost_usd=_estimate_cost(self.agent.model, in_tok, out_tok),
                latency_ms=latency_ms,
                input_preview=(prompt or "")[:280],
                output_preview=(response or "")[:280],
            )
            asyncio.create_task(save_execution_log(log))
            await event_bus.publish("execution_log", log.model_dump())
        except Exception as e:
            logger.warning("execution log failed: %s", e)

    async def send_message(self, project_id: str, content: str, msg_type: str = "chat", mentions: Optional[list[str]] = None, channel: str = "general", thread_id: Optional[str] = None):
        msg = Message(
            project_id=project_id,
            sender_id=self.id,
            sender_name=self.name,
            sender_role=str(self.agent.role),
            content=content,
            msg_type=msg_type,
            mentions=mentions or [],
            channel=channel,
            thread_id=thread_id,
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
        await self.set_status(AgentStatus.idle)

    def _system_prompt(self) -> str:
        return (
            f"You are {self.name}, a {self.agent.role} in an AI collaboration team.\n"
            f"Personality: {self.agent.personality}\n"
            f"Skills: {', '.join(self.agent.skills)}\n"
            f"You are working on project {self.agent.project_id}.\n"
            "You communicate naturally with your teammates like a human coworker.\n"
            "Be concise, professional, and collaborative.\n"
            "You can ask questions, suggest ideas, report progress, request reviews, and help others.\n"
            "When writing files, use [ACTION] blocks: [ACTION]{\"type\":\"write_file\",\"path\":\"...\",\"content\":\"...\"}[/ACTION]"
        )
