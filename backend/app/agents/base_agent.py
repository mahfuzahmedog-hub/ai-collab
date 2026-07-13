from __future__ import annotations
import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Any, Optional
from app.models.agent import Agent, AgentStatus
from app.services.lifecycle import LifecycleEngine
from app.models.message import Message
from app.models.ops import ExecutionLog
from app.llm import llm_router
from app.llm.base import ToolCallRequest, LLMResponse
from app.core.event_bus import event_bus
from app.db.repository import save_message, save_execution_log
from app.tools.registry import tool_registry
from app.graph.engine import GraphEngine, START, END
from app.graph.types import Command
from app.memory.context import ContextManager
from app.memory.memfs import MemFS

logger = logging.getLogger(__name__)


ACTION_PATTERN = re.compile(r'\[ACTION\](.*?)\[/ACTION\]', re.DOTALL)

_TOOL_HANDLERS = {
    "web_search": lambda: __import__("app.services.tools.web_search", fromlist=["search"]).search,
    "browse": lambda: __import__("app.services.tools.browser", fromlist=["browse"]).browse,
    "screenshot": lambda: __import__("app.services.tools.browser", fromlist=["screenshot"]).screenshot,
    "browser_navigate": lambda: __import__("app.services.tools.browser", fromlist=["browser_navigate"]).browser_navigate,
    "browser_click": lambda: __import__("app.services.tools.browser", fromlist=["browser_click"]).browser_click,
    "browser_type": lambda: __import__("app.services.tools.browser", fromlist=["browser_type"]).browser_type,
    "browser_scroll": lambda: __import__("app.services.tools.browser", fromlist=["browser_scroll"]).browser_scroll,
    "browser_extract": lambda: __import__("app.services.tools.browser", fromlist=["browser_extract"]).browser_extract,
    "browser_list_tabs": lambda: __import__("app.services.tools.browser", fromlist=["browser_list_tabs"]).browser_list_tabs,
    "browser_switch_tab": lambda: __import__("app.services.tools.browser", fromlist=["browser_switch_tab"]).browser_switch_tab,
    "run_python": lambda: __import__("app.services.tools.code_exec", fromlist=["run_python"]).run_python,
    "run_shell": lambda: __import__("app.services.tools.code_exec", fromlist=["run_shell"]).run_shell,
    "coding_task": lambda: __import__("app.services.tools.code_exec", fromlist=["coding_task"]).coding_task,
    "http_get": lambda: __import__("app.services.tools.api_http", fromlist=["http_get"]).http_get,
    "http_post": lambda: __import__("app.services.tools.api_http", fromlist=["http_post"]).http_post,
    "http_put": lambda: __import__("app.services.tools.api_http", fromlist=["http_put"]).http_put,
    "http_delete": lambda: __import__("app.services.tools.api_http", fromlist=["http_delete"]).http_delete,
    "get_repo": lambda: __import__("app.services.tools.github_integration", fromlist=["get_repo"]).get_repo,
    "search_repos": lambda: __import__("app.services.tools.github_integration", fromlist=["search_repos"]).search_repos,
    "get_file_content": lambda: __import__("app.services.tools.github_integration", fromlist=["get_file_content"]).get_file_content,
    "create_issue": lambda: __import__("app.services.tools.github_integration", fromlist=["create_issue"]).create_issue,
}

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
    for key, r in _PRICING.items():
        if key in (model or ""):
            return round((in_tok / 1000) * r[0] + (out_tok / 1000) * r[1], 6)
    return 0.0


class BaseAgent:
    def __init__(self, agent: Agent):
        self.agent = agent
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._lifecycle = LifecycleEngine(agent)
        self._graph: Optional[GraphEngine] = None
        self._memfs: Optional[MemFS] = None
        self._context_mgr: Optional[ContextManager] = None

    def set_memfs(self, memfs: MemFS):
        self._memfs = memfs
        self._context_mgr = ContextManager(memfs)

    def _build_agent_graph(self) -> GraphEngine:
        builder = GraphEngine()
        builder.set_entry_point("llm_call")

        async def llm_call_node(state: dict) -> Command:
            messages = state.get("messages", [])
            temperature = state.get("temperature", 0.7)
            provider_name = state.get("provider", self.agent.provider)
            provider = llm_router.get_provider(provider_name)
            use_native = provider and provider.supports_tools
            tools = self._tools_for_provider() if use_native else []

            try:
                if use_native:
                    content = ""
                    tool_calls = []
                    async for chunk in provider.chat_stream_with_tools(
                        messages, temperature=temperature, max_tokens=4096, tools=tools,
                    ):
                        content += chunk
                    tool_calls = getattr(provider, "_last_tool_calls", [])
                    # ponytail: small/free models (e.g. groq/llama-3.1-8b-instant)
                    # can return an empty body when handed a large tool schema.
                    # Fall back to a plain no-tool call so the agent still replies
                    # instead of going silent. (Upgrade: cap tool schema width.)
                    if not content and not tool_calls and tools:
                        content = (await provider.chat(messages, temperature=temperature)) or ""
                    state["_new_content"] = content
                else:
                    response = await provider.chat(messages, temperature=temperature)
                    action_tcs = self._parse_actions_to_tool_calls(response)
                    content = re.sub(r'\[ACTION\].*?\[/ACTION\]', '', response, flags=re.DOTALL).strip()
                    state["_new_content"] = content
                    tool_calls = action_tcs

                state["_tool_calls"] = tool_calls
                state["_has_tool_calls"] = len(tool_calls) > 0
                if content:
                    state.setdefault("response", "")
                    state["response"] += content
            except Exception as e:
                logger.error("Agent %s llm_call error: %s", self.name, e)
                state["_tool_calls"] = []
                state["_has_tool_calls"] = False
                if not state.get("response"):
                    # ponytail: single no-tool retry so a tool-flow failure
                    # still yields a usable reply instead of an error string.
                    # Strip tool/assistant-tool_call messages so the plain call
                    # isn't rejected by providers that forbid orphan tool roles.
                    retry_messages = [m for m in messages if m.get("role") in ("system", "user")]
                    try:
                        state["_new_content"] = (await provider.chat(retry_messages, temperature=temperature)) or ""
                    except Exception:
                        state["_new_content"] = "I encountered an error processing your request."

            return Command()

        async def route_node(state: dict) -> Command:
            if state.get("_has_tool_calls"):
                return Command(goto="tool_exec")
            return Command(goto=END)

        async def tool_exec_node(state: dict) -> Command:
            tool_calls = state.get("_tool_calls", [])
            messages = state.get("messages", [])
            results = []
            for tc in tool_calls:
                result = await self._handle_tool_call(tc, state.get("project_id", self.agent.project_id))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result or "Done."})
                results.append({"tool_call_id": tc.id, "result": result})
            state["_tool_calls"] = []
            state["_has_tool_calls"] = False
            state["_tool_results"] = results
            return Command()

        builder.add_node("llm_call", llm_call_node)
        builder.add_node("route", route_node)
        builder.add_node("tool_exec", tool_exec_node)
        builder.add_edge("llm_call", "route")
        builder.add_conditional_edges("route", lambda s: "tool_exec" if s.get("_has_tool_calls") else END, {"tool_exec": "tool_exec"})
        builder.add_edge("tool_exec", "llm_call")
        builder.set_finish_point("route")
        return builder

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

    def _parse_action_blocks(self, text: str) -> list[dict]:
        actions = []
        for match in ACTION_PATTERN.finditer(text):
            try:
                actions.append(json.loads(match.group(1).strip()))
            except json.JSONDecodeError:
                logger.warning("Failed to parse [ACTION]: %s", match.group(1)[:100])
        return actions

    def _parse_actions_to_tool_calls(self, text: str) -> list[ToolCallRequest]:
        actions = self._parse_action_blocks(text)
        tcs = []
        for i, a in enumerate(actions):
            tcs.append(ToolCallRequest(
                id=f"action_{i}",
                name=a.get("type", "unknown"),
                arguments=json.dumps({k: v for k, v in a.items() if k != "type"}),
            ))
        return tcs

    async def execute_tool(self, tool_name: str, params: dict) -> str:
        if tool_name == "delegate_to_agent":
            from app.agents.delegator import find_agent_for_task, delegate_to_agent
            team = getattr(self, "team", {})
            if not team:
                return json.dumps({"error": "No team available for delegation"})
            target_id = params.get("agent_id") or params.get("name")
            if not target_id:
                target_id = await find_agent_for_task(team, params.get("task", ""), params.get("skills_needed"))
            if not target_id:
                return json.dumps({"error": "No suitable agent found for delegation"})
            result = await delegate_to_agent(team, target_id, params.get("task", ""), params.get("context"))
            return json.dumps({"result": result})
        fn = _TOOL_HANDLERS.get(tool_name)
        if fn:
            try:
                result = await fn()(**params)
                return json.dumps(result) if not isinstance(result, str) else result
            except Exception as e:
                logger.exception("External tool %s failed", tool_name)
                return json.dumps({"error": str(e)})
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    async def _handle_tool_call(self, tc: ToolCallRequest, project_id: str) -> str:
        try:
            params = json.loads(tc.arguments) if tc.arguments else {}
        except json.JSONDecodeError:
            params = {}
        await event_bus.publish("tool_call_start", {
            "agent_id": self.id, "agent_name": self.name,
            "tool_name": tc.name, "arguments": tc.arguments,
            "tool_call_id": tc.id, "project_id": project_id,
        })
        result = await self.execute_tool(tc.name, params)
        await event_bus.publish("tool_call_result", {
            "agent_id": self.id, "agent_name": self.name,
            "tool_name": tc.name, "result": result[:500] if result else "",
            "tool_call_id": tc.id, "project_id": project_id,
        })
        return result

    def _tools_for_provider(self) -> list[dict]:
        return tool_registry.to_openai_schemas()

    def _build_messages(self, prompt: str) -> list[dict]:
        system = self._system_prompt()
        if self._context_mgr and self._memfs:
            try:
                import asyncio
                future = asyncio.ensure_future(self._context_mgr.compose_prompt(
                    project_id=self.agent.project_id,
                    base_system=system,
                    recent_history=self.agent.chat_history[-20:],
                    query=prompt,
                ))
                return future.result() if future.done() else [
                    {"role": "system", "content": system},
                    *self.agent.chat_history[-10:],
                    {"role": "user", "content": prompt},
                ]
            except Exception:
                pass
        from app.agents.context_compressor import compress_history
        history = compress_history(self.agent.chat_history)
        return [
            {"role": "system", "content": system},
            *history,
            {"role": "user", "content": prompt},
        ]

    async def _enrich_with_skills(self, prompt: str) -> str:
        from app.skills.loader import load_skills_for_prompt
        try:
            skills_text = await load_skills_for_prompt(prompt)
            if skills_text:
                return "\n" + skills_text
        except Exception:
            pass
        return ""

    async def _enrich_with_memories(self, prompt: str) -> str:
        from app.memory.manager import memory_manager
        from app.agents.prompt_builder import build_memories_block
        try:
            memories = await memory_manager.search(prompt, project_id=self.agent.project_id, agent_id=self.id, limit=5)
            if not memories:
                memories = await memory_manager.recall(self.agent.project_id, agent_id=self.id, limit=20)
            if memories:
                return "\n" + build_memories_block(memories)
        except Exception:
            pass
        return ""

    async def think(self, prompt: str, temperature: Optional[float] = None) -> str:
        await self.set_status(AgentStatus.thinking)
        messages = self._build_messages(prompt)
        recall = await self._enrich_with_memories(prompt)
        if recall:
            messages[0]["content"] += recall
        skills_block = await self._enrich_with_skills(prompt)
        if skills_block:
            messages[0]["content"] += skills_block
        _t0 = time.perf_counter()
        _status = "completed"
        try:
            provider = llm_router.get_provider(self.agent.provider)
            if not provider:
                raise RuntimeError("No LLM provider configured")
            response = await provider.chat(messages, temperature=temperature or self.agent.temperature)
            if response.startswith("["):
                raise RuntimeError(f"Provider error: {response}")
        except Exception as e:
            logger.error("Agent %s think error: %s", self.name, e)
            _status = "failed"
            response = "I received your request but the LLM service is currently unavailable."
        await self._log_execution(prompt, response, _status, int((time.perf_counter() - _t0) * 1000))
        self.agent.chat_history.append({"role": "user", "content": prompt})
        self.agent.chat_history.append({"role": "assistant", "content": response})
        self.agent.memory["short_term"].append({"prompt": prompt, "response": response})
        await self.set_status(AgentStatus.idle)
        return response

    async def think_stream(self, prompt: str, temperature: Optional[float] = None):
        await self.set_status(AgentStatus.thinking)
        messages = self._build_messages(prompt)
        recall = await self._enrich_with_memories(prompt)
        if recall:
            messages[0]["content"] += recall
        skills_block = await self._enrich_with_skills(prompt)
        if skills_block:
            messages[0]["content"] += skills_block
        full_response = ""
        try:
            async for chunk in llm_router.chat_stream(
                messages, provider=self.agent.provider,
                temperature=temperature or self.agent.temperature,
            ):
                full_response += chunk
                await event_bus.publish("stream_chunk", {
                    "agent_id": self.id, "agent_name": self.name,
                    "agent_role": str(self.role),
                    "project_id": self.agent.project_id,
                    "content": chunk, "done": False,
                })
                yield chunk
            self.agent.chat_history.append({"role": "user", "content": prompt})
            self.agent.chat_history.append({"role": "assistant", "content": full_response})
            await event_bus.publish("stream_chunk", {
                "agent_id": self.id, "agent_name": self.name,
                "agent_role": str(self.role),
                "project_id": self.agent.project_id,
                "content": "", "done": True,
            })
        except Exception as e:
            logger.error("Agent %s stream error: %s", self.name, e)
            await event_bus.publish("stream_chunk", {
                "agent_id": self.id, "agent_name": self.name,
                "agent_role": str(self.role),
                "project_id": self.agent.project_id,
                "content": "", "done": True,
            })
        await self.set_status(AgentStatus.idle)

    async def think_with_tools(self, prompt: str, temperature: Optional[float] = None):
        await self.set_status(AgentStatus.thinking)

        messages = self._build_messages(prompt)
        recall = await self._enrich_with_memories(prompt)
        if recall:
            messages[0]["content"] += recall
        skills_block = await self._enrich_with_skills(prompt)
        if skills_block:
            messages[0]["content"] += skills_block

        builder = self._build_agent_graph()
        graph = builder.compile()
        state: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature or self.agent.temperature,
            "provider": self.agent.provider,
            "project_id": self.agent.project_id,
            "agent_id": self.id,
            "response": "",
            "_tool_calls": [],
            "_has_tool_calls": False,
            "_new_content": "",
            "_tool_results": [],
        }

        full_response = ""
        first_content = True
        _t0 = time.perf_counter()

        try:
            async for snapshot in graph.stream(state):
                new_content = snapshot.get("_new_content", "")
                if new_content:
                    if first_content:
                        full_response = new_content
                        first_content = False
                    else:
                        full_response += new_content
                    yield new_content
                    state["_new_content"] = ""
        except Exception as e:
            logger.error("Agent %s graph execution error: %s", self.name, e)
            if not full_response:
                yield "I encountered an error processing your request."
        finally:
            latency = int((time.perf_counter() - _t0) * 1000)
            last_response = full_response or state.get("response", "")
            await self._log_execution(prompt, last_response, "completed", latency)
            self.agent.chat_history.append({"role": "user", "content": prompt})
            self.agent.chat_history.append({"role": "assistant", "content": last_response})
            if last_response:
                self.agent.memory["short_term"].append({"prompt": prompt, "response": last_response})
            asyncio.create_task(self._save_conversation_memories(prompt, last_response))
            asyncio.create_task(self._trigger_curation(prompt, last_response))
            await self.set_status(AgentStatus.idle)

    async def _save_conversation_memories(self, user_input: str, response: str):
        from app.memory.manager import memory_manager
        try:
            await memory_manager.save({
                "type": "conversation",
                "content": f"User: {user_input[:500]}\nAssistant: {response[:500]}",
                "scope": "project",
                "source": "conversation",
                "project_id": self.agent.project_id,
                "agent_id": self.id,
                "importance": 0.6,
                "tags": ["conversation", self.agent.provider or ""],
            })
        except Exception as e:
            logger.warning("save_conversation_memories failed: %s", e)

    async def _trigger_curation(self, user_input: str, response: str):
        from app.curation.loop import run_curation_loop
        try:
            await run_curation_loop(
                user_msg=user_input,
                agent_resp=response,
                project_id=self.agent.project_id,
                agent_id=self.id,
                user_id="default",
            )
        except Exception as e:
            logger.warning("curation loop failed: %s", e)

    async def _log_execution(self, prompt: str, response: str, status: str, latency_ms: int):
        try:
            in_tok = _estimate_tokens(prompt)
            out_tok = _estimate_tokens(response)
            log = ExecutionLog(
                project_id=self.agent.project_id,
                agent_id=self.id, agent_name=self.name,
                action="llm_call", model=self.agent.model,
                provider=self.agent.provider, status=status,
                input_tokens=in_tok, output_tokens=out_tok,
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
            project_id=project_id, sender_id=self.id,
            sender_name=self.name, sender_role=str(self.agent.role),
            content=content, msg_type=msg_type,
            mentions=mentions or [], channel=channel, thread_id=thread_id,
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
        from app.agents.prompt_builder import build_system_prompt
        return build_system_prompt(
            name=self.name,
            role=str(self.agent.role),
            personality=self.agent.personality,
            skills=self.agent.skills,
            project_id=self.agent.project_id,
            mission=self.agent.mission,
        )
