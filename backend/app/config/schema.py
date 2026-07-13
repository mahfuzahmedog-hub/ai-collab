from __future__ import annotations
from typing import Any


CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "llm_default_provider": {"type": "string"},
        "llm_default_model": {"type": "string"},
        "data_dir": {"type": "string"},
        "plugins_dir": {"type": "string"},
        "gateway_host": {"type": "string"},
        "gateway_port": {"type": "integer", "minimum": 1, "maximum": 65535},
        "gateway_auth_mode": {"type": "string", "enum": ["shared_secret", "tailscale", "trusted_proxy", "none"]},
        "gateway_shared_secret": {"type": "string"},
        "channels": {"type": "object"},
        "tools": {"type": "object"},
        "sandbox_mode": {"type": "string", "enum": ["subprocess", "docker", "ssh", "none"]},
    },
    "required": ["llm_default_provider"],
}
