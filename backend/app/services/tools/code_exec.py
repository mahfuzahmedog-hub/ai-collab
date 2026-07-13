from __future__ import annotations
import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

_BLOCKED_PATTERNS = [
    "rm -rf /", "mkfs", "dd if=", "fork bomb", "> /dev/", "sudo",
    ":(){:|:&};:", "chmod 777 /", ">|",
]
_MAX_OUTPUT_LENGTH = 10000


def _is_blocked(command: str) -> str:
    for pat in _BLOCKED_PATTERNS:
        if pat in command.lower():
            return f"Command blocked: pattern '{pat}' is not allowed"
    return ""


class SandboxedExecutor:
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = work_dir or tempfile.mkdtemp(prefix="sandbox_")

    async def run_python(self, code: str, timeout: int = 30) -> dict:
        loop = asyncio.get_event_loop()

        def _run():
            path = os.path.join(self.work_dir, f"script_{uuid.uuid4().hex[:8]}.py")
            try:
                os.makedirs(self.work_dir, exist_ok=True)
                with open(path, "w") as f:
                    f.write(code)
                proc = subprocess.run(
                    [sys.executable or "python", path],
                    capture_output=True, text=True, timeout=timeout,
                    cwd=self.work_dir,
                )
                return {
                    "stdout": proc.stdout[-_MAX_OUTPUT_LENGTH:],
                    "stderr": proc.stderr[-_MAX_OUTPUT_LENGTH:],
                    "exit_code": proc.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"stdout": "", "stderr": "", "exit_code": -1, "error": f"Timed out after {timeout}s"}
            except Exception as e:
                return {"stdout": "", "stderr": "", "exit_code": -1, "error": str(e)}
            finally:
                try:
                    os.unlink(path)
                except OSError:
                    pass

        return await loop.run_in_executor(None, _run)

    async def run_shell(self, command: str, timeout: int = 30) -> dict:
        blocked = _is_blocked(command)
        if blocked:
            return {"stdout": "", "stderr": "", "exit_code": -1, "error": blocked}

        loop = asyncio.get_event_loop()

        def _run():
            try:
                proc = subprocess.run(
                    command, shell=True, capture_output=True, text=True, timeout=timeout,
                    cwd=self.work_dir,
                )
                return {
                    "stdout": proc.stdout[-_MAX_OUTPUT_LENGTH:],
                    "stderr": proc.stderr[-_MAX_OUTPUT_LENGTH:],
                    "exit_code": proc.returncode,
                }
            except subprocess.TimeoutExpired:
                return {"stdout": "", "stderr": "", "exit_code": -1, "error": f"Timed out after {timeout}s"}
            except Exception as e:
                return {"stdout": "", "stderr": "", "exit_code": -1, "error": str(e)}

        return await loop.run_in_executor(None, _run)

    async def write_file(self, path: str, content: str) -> dict:
        full_path = os.path.join(self.work_dir, path)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
            return {"path": path, "size": len(content), "success": True}
        except Exception as e:
            return {"error": str(e)}

    async def read_file(self, path: str) -> dict:
        full_path = os.path.join(self.work_dir, path)
        try:
            with open(full_path, "r") as f:
                content = f.read()
            return {"path": path, "content": content[-_MAX_OUTPUT_LENGTH:], "size": len(content)}
        except FileNotFoundError:
            return {"error": f"File not found: {path}"}
        except Exception as e:
            return {"error": str(e)}

    async def list_files(self, path: str = ".") -> dict:
        full_path = os.path.join(self.work_dir, path)
        try:
            files = []
            for root, dirs, fnames in os.walk(full_path):
                for fname in fnames:
                    fpath = os.path.relpath(os.path.join(root, fname), self.work_dir)
                    fsize = os.path.getsize(os.path.join(root, fname))
                    files.append({"path": fpath, "size": fsize})
            return {"files": files, "count": len(files)}
        except Exception as e:
            return {"error": str(e)}

    async def git_init(self) -> dict:
        try:
            proc = subprocess.run(
                ["git", "init"], capture_output=True, text=True, cwd=self.work_dir, timeout=10,
            )
            proc = subprocess.run(
                ["git", "config", "user.email", "sandbox@aios.local"],
                capture_output=True, text=True, cwd=self.work_dir, timeout=10,
            )
            proc = subprocess.run(
                ["git", "config", "user.name", "AIOS Sandbox"],
                capture_output=True, text=True, cwd=self.work_dir, timeout=10,
            )
            return {"success": True}
        except Exception as e:
            return {"error": str(e)}

    async def git_commit(self, message: str) -> dict:
        try:
            subprocess.run(["git", "add", "-A"], capture_output=True, cwd=self.work_dir, timeout=10)
            proc = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True, text=True, cwd=self.work_dir, timeout=10,
            )
            return {"stdout": proc.stdout, "returncode": proc.returncode}
        except Exception as e:
            return {"error": str(e)}

    def cleanup(self):
        shutil.rmtree(self.work_dir, ignore_errors=True)


_sandbox = SandboxedExecutor()


async def run_python(code: str, timeout: int = 30) -> dict:
    return await _sandbox.run_python(code, timeout)


async def run_shell(command: str, timeout: int = 30) -> dict:
    return await _sandbox.run_shell(command, timeout)


async def coding_task(task: str, context: Optional[dict] = None) -> dict:
    from app.llm import llm_router
    prompt = f"""You are a coding agent. Plan and implement the following task:

{task}

Context: {json.dumps(context or {})[:1000]}

Return a JSON plan:
{{"approach": "brief approach", "files": [{{"path": "...", "description": "..."}}], "steps": ["step1", "step2"]}}"""
    provider = llm_router.get_provider()
    if not provider:
        return {"error": "No LLM provider"}
    response = await provider.chat([
        {"role": "system", "content": "You are a senior software engineer."},
        {"role": "user", "content": prompt},
    ], temperature=0.3)
    try:
        match = re.search(r'\{.*\}', response, re.DOTALL)
        plan = json.loads(match.group()) if match else {"approach": response[:500]}
        return {"plan": plan, "sandbox_dir": _sandbox.work_dir}
    except Exception as e:
        return {"plan": {"approach": response[:500]}, "sandbox_dir": _sandbox.work_dir}
