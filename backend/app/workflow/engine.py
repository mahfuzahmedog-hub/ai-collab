from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Optional

from app.workflow.types import Workflow, WorkflowNode, NodeType
from app.llm import llm_router

logger = logging.getLogger(__name__)


class WorkflowEngine:
    def __init__(self):
        self._node_handlers: dict[NodeType, callable] = {
            NodeType.llm: self._handle_llm,
            NodeType.agent: self._handle_agent,
            NodeType.tool: self._handle_tool,
            NodeType.code: self._handle_code,
            NodeType.http: self._handle_http,
            NodeType.function: self._handle_function,
            NodeType.if_node: self._handle_if,
            NodeType.loop: self._handle_loop,
        }

    def register_handler(self, node_type: NodeType, handler: callable):
        self._node_handlers[node_type] = handler

    async def execute(self, workflow: Workflow, initial_input: dict[str, Any] = None) -> dict[str, Any]:
        context: dict[str, Any] = dict(initial_input or {})
        executed = set()
        queue = [n.id for n in workflow.entry_nodes()]
        while queue:
            node_id = queue.pop(0)
            if node_id in executed:
                continue
            node = workflow.get_node(node_id)
            if not node:
                continue
            handler = self._node_handlers.get(node.type)
            if not handler:
                logger.warning("No handler for node type: %s", node.type)
                continue
            try:
                result = await handler(node, context)
                context[f"node_{node_id}"] = result
            except Exception as e:
                logger.error("Node %s failed: %s", node_id, e)
                context[f"node_{node_id}_error"] = str(e)
            executed.add(node_id)
            for edge in workflow.outgoing(node_id):
                if edge.condition:
                    if not self._eval_condition(edge.condition, context):
                        continue
                if edge.target not in executed:
                    queue.append(edge.target)
        return context

    def _eval_condition(self, condition: str, context: dict) -> bool:
        try:
            safe_globals = {"__builtins__": {}}
            return bool(eval(condition, safe_globals, context))
        except Exception:
            return False

    async def _handle_llm(self, node: WorkflowNode, context: dict) -> Any:
        prompt = node.config.get("prompt", "")
        for k, v in context.items():
            prompt = prompt.replace(f"{{{{{k}}}}}", str(v))
        provider = llm_router.get_provider()
        if not provider:
            return {"error": "No LLM provider"}
        response = await provider.chat([
            {"role": "system", "content": node.config.get("system", "You are a helpful assistant.")},
            {"role": "user", "content": prompt},
        ], temperature=node.config.get("temperature", 0.7))
        return {"content": response}

    async def _handle_agent(self, node: WorkflowNode, context: dict) -> Any:
        from app.services.agent_manager import agent_manager
        agent_id = node.config.get("agent_id", "")
        message = node.config.get("message", "")
        for k, v in context.items():
            message = message.replace(f"{{{{{k}}}}}", str(v))
        agent = await agent_manager.get_agent(agent_id)
        if agent:
            return {"delegated": agent_id, "message": message}
        return {"error": f"Agent {agent_id} not found"}

    async def _handle_tool(self, node: WorkflowNode, context: dict) -> Any:
        from app.tools.registry import tool_registry
        tool_name = node.config.get("tool", "")
        params = node.config.get("params", {})
        for k, v in list(params.items()):
            if isinstance(v, str):
                for ck, cv in context.items():
                    params[k] = params[k].replace(f"{{{{{ck}}}}}", str(cv))
        tool_def = tool_registry.get(tool_name)
        if not tool_def:
            return {"error": f"Tool {tool_name} not found"}
        from app.agents.base_agent import _TOOL_HANDLERS
        handler = _TOOL_HANDLERS.get(tool_name)
        if handler:
            try:
                fn = handler()
                result = await fn(**params)
                return {"result": result}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "No handler for tool"}

    async def _handle_code(self, node: WorkflowNode, context: dict) -> Any:
        code = node.config.get("code", "")
        try:
            safe_globals = {"__builtins__": {}, "context": context, "result": {}}
            exec(code, safe_globals)
            return safe_globals.get("result", {})
        except Exception as e:
            return {"error": str(e)}

    async def _handle_http(self, node: WorkflowNode, context: dict) -> Any:
        import httpx
        url = node.config.get("url", "")
        method = node.config.get("method", "GET")
        body = node.config.get("body")
        try:
            resp = await httpx.request(method, url, json=body, timeout=30)
            return {"status": resp.status_code, "body": resp.text[:5000]}
        except Exception as e:
            return {"error": str(e)}

    async def _handle_function(self, node: WorkflowNode, context: dict) -> Any:
        expr = node.config.get("expression", "true")
        return {"value": self._eval_condition(expr, context)}

    async def _handle_if(self, node: WorkflowNode, context: dict) -> Any:
        condition = node.config.get("condition", "true")
        return {"condition": self._eval_condition(condition, context), "value": None}

    async def _handle_loop(self, node: WorkflowNode, context: dict) -> Any:
        times = node.config.get("times", 1)
        results = []
        for i in range(times):
            context["loop_index"] = i
            results.append({"index": i})
        return {"iterations": times, "results": results}


workflow_engine = WorkflowEngine()
