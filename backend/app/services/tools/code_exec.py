import asyncio
import subprocess
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

_BLOCKED_PATTERNS = [
    "rm -rf /", "mkfs", "dd if=", "fork bomb", "> /dev/", "| sh", "sudo",
    ":(){:|:&};:", "chmod 777 /", "wget ", "curl ", ">|",
]


def _is_blocked(command: str) -> str:
    for pat in _BLOCKED_PATTERNS:
        if pat in command.lower():
            return f"Command blocked: pattern '{pat}' is not allowed"
    return ""


async def run_python(code: str, timeout: int = 30) -> dict:
    loop = asyncio.get_event_loop()

    def _run():
        fd, path = tempfile.mkstemp(suffix=".py", prefix="run_")
        try:
            os.write(fd, code.encode("utf-8"))
            os.close(fd)
            proc = subprocess.run(
                ["python", path],
                capture_output=True, text=True, timeout=timeout,
            )
            return {"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode, "error": None}
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


async def run_shell(command: str, timeout: int = 30) -> dict:
    blocked = _is_blocked(command)
    if blocked:
        return {"stdout": "", "stderr": "", "exit_code": -1, "error": blocked}

    loop = asyncio.get_event_loop()

    def _run():
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout,
            )
            return {"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode, "error": None}
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "", "exit_code": -1, "error": f"Timed out after {timeout}s"}
        except Exception as e:
            return {"stdout": "", "stderr": "", "exit_code": -1, "error": str(e)}

    return await loop.run_in_executor(None, _run)
