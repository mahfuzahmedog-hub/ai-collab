from __future__ import annotations
import asyncio
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from typing import Optional


class SandboxBackend(ABC):
    @abstractmethod
    async def run(self, command: list[str], timeout: int = 30) -> dict:
        pass


class SubprocessSandbox(SandboxBackend):
    async def run(self, command: list[str], timeout: int = 30) -> dict:
        loop = asyncio.get_event_loop()
        def _run():
            try:
                proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
                return {"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode}
            except subprocess.TimeoutExpired:
                return {"stdout": "", "stderr": "", "exit_code": -1, "error": "timeout"}
            except Exception as e:
                return {"error": str(e)}
        return await loop.run_in_executor(None, _run)


class DockerSandbox(SandboxBackend):
    def __init__(self, image: str = "python:3.11-slim", workdir: str = "/workspace"):
        self.image = image
        self.workdir = workdir

    async def run(self, command: list[str], timeout: int = 30) -> dict:
        docker_cmd = [
            "docker", "run", "--rm", "-v", f"{os.path.abspath(self.workdir)}:/workspace",
            self.image, *command,
        ]
        return await SubprocessSandbox().run(docker_cmd, timeout)


class SandboxManager:
    def __init__(self, mode: str = "subprocess"):
        self.mode = mode
        self._backends = {
            "subprocess": SubprocessSandbox(),
            "docker": DockerSandbox(),
        }

    def get_backend(self) -> SandboxBackend:
        return self._backends.get(self.mode, SubprocessSandbox())

    async def run(self, command: list[str], timeout: int = 30) -> dict:
        return await self.get_backend().run(command, timeout)


sandbox_manager = SandboxManager()
