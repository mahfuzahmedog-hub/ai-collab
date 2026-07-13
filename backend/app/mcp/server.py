from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Callable, Optional

from app.mcp.types import MCPTool, MCPResource, MCPPrompt, JSONRPCRequest, JSONRPCResponse

logger = logging.getLogger(__name__)


class MCPServer:
    def __init__(self, name: str = "aios-mcp"):
        self.name = name
        self._tools: dict[str, dict] = {}
        self._resources: dict[str, dict] = {}
        self._prompts: dict[str, dict] = {}

    def register_tool(self, tool: MCPTool, handler: Callable[[dict], Any]):
        self._tools[tool.name] = {"spec": tool, "handler": handler}

    def register_resource(self, resource: MCPResource, loader: Callable[[], Any] = None):
        self._resources[resource.uri] = {"spec": resource, "loader": loader or (lambda: "")}

    def register_prompt(self, prompt: MCPPrompt, renderer: Callable[[dict], str] = None):
        self._prompts[prompt.name] = {"spec": prompt, "renderer": renderer or (lambda a: "")}

    async def handle(self, raw: dict) -> dict:
        req = JSONRPCRequest(**raw)
        method = req.method

        if method == "initialize":
            return JSONRPCResponse(id=req.id, result={
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": {"name": self.name, "version": "1.0.0"},
            }).to_dict()

        if method == "ping":
            return JSONRPCResponse(id=req.id, result={}).to_dict()

        if method == "tools/list":
            tools = [t["spec"].__dict__ for t in self._tools.values()]
            return JSONRPCResponse(id=req.id, result={"tools": tools}).to_dict()

        if method == "tools/call":
            name = req.params.get("name", "")
            args = req.params.get("arguments", {})
            tool = self._tools.get(name)
            if not tool:
                return JSONRPCResponse(id=req.id, error={"code": -32601, "message": f"Tool {name} not found"}).to_dict()
            try:
                result = await tool["handler"](args) if asyncio.iscoroutinefunction(tool["handler"]) else tool["handler"](args)
                return JSONRPCResponse(id=req.id, result={"content": [{"type": "text", "text": str(result)}]}).to_dict()
            except Exception as e:
                return JSONRPCResponse(id=req.id, error={"code": -32603, "message": str(e)}).to_dict()

        if method == "resources/list":
            resources = [r["spec"].__dict__ for r in self._resources.values()]
            return JSONRPCResponse(id=req.id, result={"resources": resources}).to_dict()

        if method == "resources/read":
            uri = req.params.get("uri", "")
            res = self._resources.get(uri)
            if not res:
                return JSONRPCResponse(id=req.id, error={"code": -32602, "message": "Resource not found"}).to_dict()
            content = res["loader"]()
            return JSONRPCResponse(id=req.id, result={"contents": [{"uri": uri, "mimeType": res["spec"].mime_type, "text": str(content)}]}).to_dict()

        if method == "prompts/list":
            prompts = [p["spec"].__dict__ for p in self._prompts.values()]
            return JSONRPCResponse(id=req.id, result={"prompts": prompts}).to_dict()

        if method == "prompts/get":
            name = req.params.get("name", "")
            args = req.params.get("arguments", {})
            prompt = self._prompts.get(name)
            if not prompt:
                return JSONRPCResponse(id=req.id, error={"code": -32602, "message": "Prompt not found"}).to_dict()
            text = prompt["renderer"](args)
            return JSONRPCResponse(id=req.id, result={"messages": [{"role": "user", "content": {"type": "text", "text": text}}]}).to_dict()

        return JSONRPCResponse(id=req.id, error={"code": -32601, "message": f"Method not found: {method}"}).to_dict()


mcp_server = MCPServer()
