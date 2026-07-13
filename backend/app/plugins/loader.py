from __future__ import annotations
import asyncio
import importlib.util
import json
import logging
import os
import sys
from typing import Optional

from app.plugins.base import Plugin, PluginManifest, parse_manifest

logger = logging.getLogger(__name__)


class PluginLoader:
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = plugin_dir
        self._plugins: dict[str, Plugin] = {}

    def discover(self) -> list[PluginManifest]:
        manifests = []
        if not os.path.isdir(self.plugin_dir):
            return manifests
        for entry in os.listdir(self.plugin_dir):
            manifest_path = os.path.join(self.plugin_dir, entry, "aios.plugin.json")
            if os.path.isfile(manifest_path):
                try:
                    manifests.append(parse_manifest(manifest_path))
                except Exception as e:
                    logger.warning("Failed to parse plugin manifest %s: %s", manifest_path, e)
        return manifests

    async def load(self, manifest: PluginManifest) -> Optional[Plugin]:
        plugin_path = os.path.join(self.plugin_dir, manifest.name)
        entry = os.path.join(plugin_path, manifest.entrypoint or "main.py")
        if not os.path.isfile(entry):
            logger.warning("Plugin entrypoint not found: %s", entry)
            return None
        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{manifest.name}", entry)
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugin_{manifest.name}"] = module
            spec.loader.exec_module(module)
            plugin = module.register(manifest) if hasattr(module, "register") else Plugin(manifest)
            await plugin.startup()
            self._plugins[manifest.name] = plugin
            logger.info("Loaded plugin: %s v%s", manifest.name, manifest.version)
            return plugin
        except Exception as e:
            logger.error("Plugin load failed: %s: %s", manifest.name, e)
            return None

    async def load_all(self) -> list[str]:
        loaded = []
        for manifest in self.discover():
            plugin = await self.load(manifest)
            if plugin:
                loaded.append(manifest.name)
        return loaded

    async def unload(self, name: str) -> bool:
        plugin = self._plugins.pop(name, None)
        if plugin:
            await plugin.shutdown()
            return True
        return False

    def get(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)


plugin_loader = PluginLoader()
