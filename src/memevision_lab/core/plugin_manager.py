from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


@dataclass(frozen=True)
class PluginManifest:
    id: str
    name: str
    description: str
    category: str
    author: str
    version: str
    entrypoint: str
    preview: str | None
    required_trackers: tuple[str, ...]
    tags: tuple[str, ...]
    path: Path


class PluginManager:
    def __init__(self, plugins_path: Path) -> None:
        self.plugins_path = plugins_path

    def discover(self) -> list[PluginManifest]:
        if not self.plugins_path.exists():
            return []

        manifests: list[PluginManifest] = []
        for plugin_dir in sorted(self.plugins_path.iterdir()):
            manifest_path = plugin_dir / "manifest.json"
            if not plugin_dir.is_dir() or not manifest_path.exists():
                continue
            manifests.append(self._load_manifest(manifest_path))
        return manifests

    def load_plugin(self, manifest: PluginManifest) -> Any:
        entrypoint_path = manifest.path / manifest.entrypoint
        module = self._load_module(manifest.id, entrypoint_path)
        plugin_class = getattr(module, "Plugin")
        return plugin_class()

    def _load_manifest(self, manifest_path: Path) -> PluginManifest:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        return PluginManifest(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            category=data.get("category", "misc"),
            author=data.get("author", "Unknown"),
            version=data.get("version", "0.0.0"),
            entrypoint=data.get("entrypoint", "plugin.py"),
            preview=data.get("preview"),
            required_trackers=tuple(data.get("required_trackers", [])),
            tags=tuple(data.get("tags", [])),
            path=manifest_path.parent,
        )

    def _load_module(self, plugin_id: str, entrypoint_path: Path) -> ModuleType:
        module_name = f"memevision_plugin_{plugin_id}"
        spec = importlib.util.spec_from_file_location(module_name, entrypoint_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load plugin entrypoint: {entrypoint_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
