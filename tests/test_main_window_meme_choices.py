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


def test_prepare_local_media_copies_external_file_to_local_assets(tmp_path):
    _write_meme_config(tmp_path, "thumbs_up", "existing", "hand")
    _write_plugin_manifest(tmp_path)
    external_file = tmp_path / "downloads" / "funny.gif"
    external_file.parent.mkdir()
    external_file.write_bytes(b"gif-bytes")
    app = QApplication.instance() or QApplication([])
    window = MainWindow(PluginManager(tmp_path / "plugins"))

    try:
        relative_path = window._prepare_local_media(external_file, "hand", "memes", "Funny Meme")
        copied_file = tmp_path / relative_path

        assert relative_path == "local_assets/memes/hands/funny_meme.gif"
        assert copied_file.read_bytes() == b"gif-bytes"
    finally:
        window.close()
        app.processEvents()


def test_prepare_local_media_keeps_existing_local_asset_path(tmp_path):
    _write_meme_config(tmp_path, "thumbs_up", "existing", "hand")
    _write_plugin_manifest(tmp_path)
    local_file = tmp_path / "local_assets" / "memes" / "hands" / "existing.gif"
    local_file.parent.mkdir(parents=True)
    local_file.write_bytes(b"gif-bytes")
    app = QApplication.instance() or QApplication([])
    window = MainWindow(PluginManager(tmp_path / "plugins"))

    try:
        relative_path = window._prepare_local_media(local_file, "hand", "memes", "Other Name")

        assert relative_path == "local_assets/memes/hands/existing.gif"
        assert not (tmp_path / "local_assets" / "memes" / "hands" / "other_name.gif").exists()
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
