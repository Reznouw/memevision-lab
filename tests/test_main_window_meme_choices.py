from __future__ import annotations

import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from memevision_lab.core.plugin_manager import PluginManager
from memevision_lab.ui.main_window import MainWindow


def test_meme_choices_include_missing_assets_and_label_them(tmp_path):
    _write_meme_config(tmp_path, "thumbs_up", "missing_thumb", "hand")
    _write_plugin_manifest(tmp_path)
    app = QApplication.instance() or QApplication([])
    window = MainWindow(PluginManager(tmp_path / "plugins"))

    try:
        assert [meme.id for meme in window.meme_choices] == ["missing_thumb"]
        assert window._meme_choices_for_mode("hand")[0].id == "missing_thumb"
        assert "asset missing" in window._meme_choice_label(window.meme_choices[0])
    finally:
        window.close()
        app.processEvents()


def test_append_meme_entry_and_reload_selects_new_meme(tmp_path):
    _write_meme_config(tmp_path, "thumbs_up", "existing", "hand")
    _write_plugin_manifest(tmp_path)
    asset_path = tmp_path / "local_assets" / "memes" / "hands" / "new.gif"
    asset_path.parent.mkdir(parents=True)
    asset_path.write_bytes(b"not-a-real-gif")
    app = QApplication.instance() or QApplication([])
    window = MainWindow(PluginManager(tmp_path / "plugins"))

    try:
        window._append_meme_entry(
            "thumbs_up",
            {
                "id": "new_meme",
                "name": "New Meme",
                "asset": "local_assets/memes/hands/new.gif",
                "sound": None,
                "input_type": "hand",
                "cooldown_seconds": 1.0,
                "category": "test",
            },
        )
        window._reload_meme_choices("new_meme")

        assert any(meme.id == "new_meme" for meme in window.meme_choices)
        assert "new_meme" in window.selected_meme_ids
    finally:
        window.close()
        app.processEvents()


def _write_meme_config(root, trigger: str, meme_id: str, input_type: str) -> None:
    config_dir = root / "configs" / "memes" / "by_trigger"
    config_dir.mkdir(parents=True)
    (config_dir / f"{trigger}.json").write_text(
        json.dumps(
            [
                {
                    "id": meme_id,
                    "name": meme_id.replace("_", " ").title(),
                    "asset": f"local_assets/{meme_id}.gif",
                    "input_type": input_type,
                }
            ]
        ),
        encoding="utf-8",
    )


def _write_plugin_manifest(root) -> None:
    plugin_dir = root / "plugins" / "meme_reactions"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "id": "meme_reactions",
                "name": "Meme Reactions",
                "description": "Test plugin",
                "category": "reaction",
                "entrypoint": "plugin.py",
                "required_trackers": ["hands"],
                "tags": ["test"],
            }
        ),
        encoding="utf-8",
    )
    (plugin_dir / "plugin.py").write_text(
        "class Plugin:\n    pass\n",
        encoding="utf-8",
    )
