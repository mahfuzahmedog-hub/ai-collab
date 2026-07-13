from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Optional

from app.gateway.protocol import GatewayFrame, FrameType
from app.gateway.auth import GatewayAuth, AuthMode

logger = logging.getLogger(__name__)


class GatewayServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 9100, auth: Optional[GatewayAuth] = None):
        self.host = host
        self.port = port
        self.auth = auth or GatewayAuth()
        self._server: Optional[asyncio.AbstractServer] = None
        self._connections: dict[str, asyncio.Queue] = {}
        self._handlers: dict[str, callable] = {}

    def on(self, method: str, handler: callable):
        self._handlers[method] = handler

    async def start(self):
        self._server = await asyncio.start_server(
            self._handle_client, self.host, self.port
        )
        logger.info("Gateway server listening on %s:%s", self.host, self.port)

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Gateway server stopped")

    async def broadcast(self, frame: GatewayFrame):
        for conn_id, queue in self._connections.items():
            await queue.put(frame)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.Writer):
        conn_id = f"conn-{id(writer):x}"
        queue: asyncio.Queue = asyncio.Queue()
        self._connections[conn_id] = queue
        logger.info("Gateway client connected: %s", conn_id)

        async def writer_task():
            try:
                while True:
                    frame = await queue.get()
                    data = frame.to_json() + "\n"
                    writer.write(data.encode())
                    await writer.drain()
            except (ConnectionResetError, BrokenPipeError):
                pass
            finally:
                self._connections.pop(conn_id, None)

        write_task = asyncio.create_task(writer_task())
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    frame = GatewayFrame.from_json(line.decode().strip())
                    await self._process_frame(frame, conn_id, writer)
                except Exception as e:
                    logger.warning("Gateway frame error: %s", e)
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            write_task.cancel()
            self._connections.pop(conn_id, None)
            try:
                writer.close()
            except Exception:
                pass

    async def _process_frame(self, frame: GatewayFrame, conn_id: str, writer: asyncio.Writer):
        if frame.type == FrameType.ping:
            pong = GatewayFrame.pong(frame.id)
            writer.write((pong.to_json() + "\n").encode())
            await writer.drain()
        elif frame.type == FrameType.request:
            handler = self._handlers.get(frame.method)
            if handler:
                try:
                    result = await handler(frame.params, conn_id)
                    resp = GatewayFrame.response(frame.id, result=result)
                except Exception as e:
                    resp = GatewayFrame.response(frame.id, error={"message": str(e)})
            else:
                resp = GatewayFrame.response(frame.id, error={"message": f"Unknown method: {frame.method}"})
            writer.write((resp.to_json() + "\n").encode())
            await writer.drain()
