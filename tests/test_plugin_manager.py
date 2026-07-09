from __future__ import annotations

import json

from memevision_lab.core.plugin_manager import PluginManager


def test_discovers_plugin_manifest(tmp_path):
    plugin_dir = tmp_path / "plugins" / "demo"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "id": "demo",
                "name": "Demo",
                "description": "Test plugin",
                "category": "test",
                "entrypoint": "plugin.py",
                "required_trackers": ["hands"],
                "tags": ["example"],
            }
        ),
        encoding="utf-8",
    )

    plugins = PluginManager(tmp_path / "plugins").discover()

    assert len(plugins) == 1
    assert plugins[0].id == "demo"
    assert plugins[0].required_trackers == ("hands",)
    assert plugins[0].tags == ("example",)
