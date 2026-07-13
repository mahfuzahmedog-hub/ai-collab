from __future__ import annotations
import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CONFIG_PATH = os.path.expanduser("~/.config/aios/config.json")


@dataclass
class AIOSConfig:
    llm_default_provider: str = "openai"
    llm_default_model: str = "gpt-4o-mini"
    data_dir: str = "~/.local/share/aios"
    plugins_dir: str = "plugins"
    gateway_host: str = "127.0.0.1"
    gateway_port: int = 9100
    gateway_auth_mode: str = "none"
    gateway_shared_secret: str = ""
    channels: dict[str, Any] = field(default_factory=dict)
    tools: dict[str, Any] = field(default_factory=dict)
    sandbox_mode: str = "subprocess"

    def to_dict(self) -> dict:
        return {
            "llm_default_provider": self.llm_default_provider,
            "llm_default_model": self.llm_default_model,
            "data_dir": self.data_dir,
            "plugins_dir": self.plugins_dir,
            "gateway_host": self.gateway_host,
            "gateway_port": self.gateway_port,
            "gateway_auth_mode": self.gateway_auth_mode,
            "gateway_shared_secret": self.gateway_shared_secret,
            "channels": self.channels,
            "tools": self.tools,
            "sandbox_mode": self.sandbox_mode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AIOSConfig:
        return cls(
            llm_default_provider=d.get("llm_default_provider", "openai"),
            llm_default_model=d.get("llm_default_model", "gpt-4o-mini"),
            data_dir=d.get("data_dir", "~/.local/share/aios"),
            plugins_dir=d.get("plugins_dir", "plugins"),
            gateway_host=d.get("gateway_host", "127.0.0.1"),
            gateway_port=d.get("gateway_port", 9100),
            gateway_auth_mode=d.get("gateway_auth_mode", "none"),
            gateway_shared_secret=d.get("gateway_shared_secret", ""),
            channels=d.get("channels", {}),
            tools=d.get("tools", {}),
            sandbox_mode=d.get("sandbox_mode", "subprocess"),
        )


def load_config(path: str = _CONFIG_PATH) -> AIOSConfig:
    if os.path.isfile(path):
        try:
            with open(path) as f:
                data = json.load(f)
            cfg = AIOSConfig.from_dict(data)
            logger.info("Loaded config from %s", path)
            return cfg
        except Exception as e:
            logger.warning("Failed to load config %s: %s", path, e)
    env_override = _from_env()
    if env_override:
        return env_override
    return AIOSConfig()


def save_config(config: AIOSConfig, path: str = _CONFIG_PATH) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
        return True
    except Exception as e:
        logger.error("Failed to save config: %s", e)
        return False


def _from_env() -> Optional[AIOSConfig]:
    provider = os.environ.get("AIOS_LLM_PROVIDER")
    if not provider:
        return None
    return AIOSConfig(
        llm_default_provider=provider,
        llm_default_model=os.environ.get("AIOS_LLM_MODEL", "gpt-4o-mini"),
        gateway_host=os.environ.get("AIOS_GATEWAY_HOST", "127.0.0.1"),
        gateway_port=int(os.environ.get("AIOS_GATEWAY_PORT", "9100")),
    )


def validate_config(config: AIOSConfig) -> list[str]:
    errors = []
    if not config.llm_default_provider:
        errors.append("llm_default_provider is required")
    if config.gateway_port < 1 or config.gateway_port > 65535:
        errors.append("gateway_port out of range")
    if config.gateway_auth_mode not in ("shared_secret", "tailscale", "trusted_proxy", "none"):
        errors.append("gateway_auth_mode invalid")
    return errors


def load_and_validate() -> tuple[AIOSConfig, list[str]]:
    cfg = load_config()
    errors = validate_config(cfg)
    return cfg, errors
