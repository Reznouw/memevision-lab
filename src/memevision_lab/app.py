from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from memevision_lab.core.plugin_manager import PluginManager
from memevision_lab.ui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MemeVision Lab")

    root_path = _discover_project_root()
    theme_path = Path(__file__).with_name("assets") / "theme.qss"
    if theme_path.exists():
        app.setStyleSheet(theme_path.read_text(encoding="utf-8"))

    plugin_manager = PluginManager(root_path / "plugins")
    window = MainWindow(plugin_manager=plugin_manager)
    window.resize(1180, 760)
    window.show()
    return app.exec()


def _discover_project_root() -> Path:
    if getattr(sys, "frozen", False):
        executable_root = Path(sys.executable).parent
        if (executable_root / "plugins").exists() or (executable_root / "configs").exists():
            return executable_root
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        if (bundle_root / "plugins").exists() or (bundle_root / "configs").exists():
            return bundle_root
        return executable_root

    current = Path.cwd()
    if (current / "plugins").exists() or (current / "pyproject.toml").exists():
        return current

    package_root = Path(__file__).resolve().parents[2]
    return package_root
