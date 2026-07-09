from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from memevision_lab.core.camera_worker import CameraWorker
from memevision_lab.core.face_tracker import FaceTrackingResult
from memevision_lab.core.gesture_sample_recorder import GestureSampleRecorder
from memevision_lab.core.hand_tracker import HandTrackingResult
from memevision_lab.core.meme_reactions import MemeReaction, MemeReactionEngine
from memevision_lab.core.plugin_manager import PluginManager, PluginManifest


class StreamWindow(QMainWindow):
    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self.setWindowTitle(title)
        self.resize(720, 520)
        self.setMinimumSize(360, 280)

        root = QFrame()
        root.setObjectName("StreamWindow")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QLabel(title)
        heading.setObjectName("StreamTitle")
        self.image_label = QLabel(message)
        self.image_label.setObjectName("StreamDisplay")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setWordWrap(True)
        self.image_label.setMinimumSize(240, 160)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.frame_scale = 1.0
        self.overlay_message = ""

        layout.addWidget(heading)
        layout.addWidget(self.image_label, 1)
        self.setCentralWidget(root)

    def set_message(self, message: str) -> None:
        self.image_label.clear()
        self.image_label.setText(message)

    def set_frame(self, frame) -> None:
        image_format = QImage.Format_RGBA8888 if frame.shape[2] == 4 else QImage.Format_RGB888
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        image = QImage(frame.data, width, height, bytes_per_line, image_format).copy()
        pixmap = QPixmap.fromImage(image)
        target_size = self.image_label.size() * self.frame_scale
        scaled = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if self.overlay_message:
            scaled = self._with_overlay(scaled, self.overlay_message)
        self.image_label.setPixmap(scaled)

    def set_frame_scale(self, scale: float) -> None:
        self.frame_scale = max(0.25, min(scale, 1.6))

    def set_overlay_message(self, message: str) -> None:
        self.overlay_message = message

    def _with_overlay(self, pixmap: QPixmap, message: str) -> QPixmap:
        painted = QPixmap(pixmap)
        painter = QPainter(painted)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(painted.rect(), QColor(0, 0, 0, 80))
        font = QFont()
        font.setBold(True)
        font.setPointSize(max(22, min(72, painted.width() // 10)))
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(painted.rect(), Qt.AlignCenter, message)
        painter.end()
        return painted

    def present_above_others(self) -> None:
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()
        self.raise_()
        self.activateWindow()
        QTimer.singleShot(1400, self._release_topmost)

    def _release_topmost(self) -> None:
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        self.show()
        self.raise_()


class MainWindow(QMainWindow):
    def __init__(self, plugin_manager: PluginManager) -> None:
        super().__init__()
        self.plugin_manager = plugin_manager
        self.project_root = plugin_manager.plugins_path.parent
        self.plugins = self.plugin_manager.discover()
        self.camera_worker: CameraWorker | None = None
        self.camera_window: StreamWindow | None = None
        self.meme_window: StreamWindow | None = None
        self.meme_windows: list[StreamWindow] = []
        self.audio_ready = False
        self.last_frame_image: QImage | None = None
        self.metric_values: dict[str, QLabel] = {}
        self.meme_reactions_mode_select: QComboBox | None = None
        self.selected_meme_ids: set[str] = set()
        self.meme_choices: list[MemeReaction] = []
        self.meme_selection_status: QLabel | None = None
        self.output_count_input: QSpinBox | None = None
        self.motion_gesture_id_input: QLineEdit | None = None
        self.start_motion_session_button: QPushButton | None = None
        self.stop_recorder_camera_button: QPushButton | None = None
        self.record_motion_button: QPushButton | None = None
        self.attach_meme_button: QPushButton | None = None
        self.recorder_status_label: QLabel | None = None
        self.record_countdown_remaining = 0
        self.recording_deadline: float | None = None
        self.recording_duration_seconds = 3.0
        self.gesture_recorder: GestureSampleRecorder | None = None

        self.setWindowTitle("MemeVision Lab")
        self.stack = QStackedWidget()
        self.home_page = self._build_home_page()
        self.catalog_page = self._build_catalog_page()
        self.session_page = self._build_session_page()
        self.recorder_page = self._build_gesture_recorder_page()
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.catalog_page)
        self.stack.addWidget(self.session_page)
        self.stack.addWidget(self.recorder_page)

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._stop_session()
        super().closeEvent(event)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(286)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(8)

        title = QLabel("MemeVision Lab")
        title.setObjectName("BrandTitle")
        subtitle = QLabel("computer vision workshop")
        subtitle.setObjectName("MutedText")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)
        layout.addWidget(self._nav_button("Home", 0))
        layout.addWidget(self._nav_button("Project Catalog", 1))
        layout.addWidget(self._nav_button("Session Console", 2))
        layout.addWidget(self._nav_button("Gesture Recorder", 3))
        layout.addStretch()

        status = QFrame()
        status.setObjectName("SidebarCard")
        status_layout = QVBoxLayout(status)
        status_layout.setContentsMargins(14, 14, 14, 14)
        status_layout.setSpacing(6)
        status_layout.addWidget(self._small_label("Lab Status", "CardTitleSmall"))
        status_layout.addWidget(self._small_label(f"{len(self.plugins)} projects available", "MutedText"))
        status_layout.addWidget(self._small_label("Launcher mode", "MutedText"))
        layout.addWidget(status)
        return sidebar

    def _nav_button(self, text: str, page_index: int) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("NavButton")
        button.clicked.connect(lambda: self.stack.setCurrentIndex(page_index))
        return button

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(44, 36, 44, 36)
        layout.setSpacing(18)

        layout.addWidget(self._page_header(
            "MemeVision Lab",
            "A desktop launcher for learning computer vision through memes, camera input, and readable Python code.",
        ))

        hero = QFrame()
        hero.setObjectName("HeroCard")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(24)

        copy = QVBoxLayout()
        copy.setSpacing(12)
        copy.addWidget(self._small_label("How the workshop runs", "SectionTitle"))
        copy.addWidget(self._small_label("1. Pick a project from the catalog.", "MutedText"))
        copy.addWidget(self._small_label("2. MemeVision opens VS Code at the source folder.", "MutedText"))
        copy.addWidget(self._small_label("3. A Camera window and Meme Output window open separately.", "MutedText"))
        copy.addWidget(self._small_label("4. Students use the app and inspect the code side by side.", "MutedText"))
        actions = QHBoxLayout()
        launch = QPushButton("Open Catalog")
        launch.setObjectName("PrimaryButton")
        launch.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        actions.addWidget(launch)
        actions.addStretch()
        copy.addLayout(actions)

        diagram = QFrame()
        diagram.setObjectName("CodePanel")
        diagram_layout = QVBoxLayout(diagram)
        diagram_layout.setContentsMargins(18, 18, 18, 18)
        diagram_layout.setSpacing(10)
        for line in (
            "MemeVision Lab",
            "├─ open VS Code",
            "├─ Camera Window",
            "└─ Meme Output Window",
        ):
            diagram_layout.addWidget(self._small_label(line, "CodeText"))
        diagram_layout.addStretch()

        hero_layout.addLayout(copy, 2)
        hero_layout.addWidget(diagram, 1)
        layout.addWidget(hero)
        layout.addWidget(self._capability_grid())
        layout.addStretch()
        return page

    def _build_catalog_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(44, 36, 44, 36)
        layout.setSpacing(16)
        layout.addWidget(self._page_header(
            "Project Catalog",
            "Choose a computer-vision mini-project. Launching opens the code and two separate runtime windows.",
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)
        for index, plugin in enumerate(self._sorted_plugins()):
            grid.addWidget(self._plugin_card(plugin), index // 2, index % 2)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _plugin_card(self, plugin: PluginManifest) -> QWidget:
        card = QFrame()
        card.setObjectName("PluginCard")
        card.setMinimumHeight(240 if plugin.id != "meme_reactions" else 310)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)
        top = QHBoxLayout()
        top.addWidget(self._small_label(plugin.category.upper(), "Badge"))
        top.addStretch()
        top.addWidget(self._small_label("READY" if plugin.id == "meme_reactions" else "CONCEPT", "StatusReady" if plugin.id == "meme_reactions" else "StatusSoon"))
        layout.addLayout(top)
        layout.addWidget(self._small_label(plugin.name, "CardTitle"))
        description = self._small_label(plugin.description, "MutedText")
        description.setWordWrap(True)
        layout.addWidget(description)
        layout.addWidget(self._small_label("Trackers: " + ", ".join(plugin.required_trackers or ("none",)), "TinyText"))
        if plugin.id == "meme_reactions":
            layout.addWidget(self._meme_reactions_config())
        layout.addStretch()
        launch = QPushButton("Launch Project" if plugin.id == "meme_reactions" else "View Concept")
        launch.setObjectName("PrimaryButton" if plugin.id == "meme_reactions" else "SecondaryButton")
        launch.clicked.connect(lambda: self._launch_project(plugin))
        layout.addWidget(launch, alignment=Qt.AlignLeft)
        return card

    def _meme_reactions_config(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("InlineConfig")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        mode_row = QHBoxLayout()
        mode_copy = QVBoxLayout()
        mode_copy.setSpacing(2)
        mode_copy.addWidget(self._small_label("Input Mode", "CardTitleSmall"))
        mode_copy.addWidget(self._small_label("Project-specific, before launch.", "TinyText"))
        self.meme_reactions_mode_select = QComboBox()
        self.meme_reactions_mode_select.setObjectName("ModeSelect")
        self.meme_reactions_mode_select.addItem("Hands only", "hand")
        self.meme_reactions_mode_select.addItem("Face only", "face")
        self.meme_reactions_mode_select.addItem("Motion only", "motion")
        self.meme_reactions_mode_select.addItem("Mixed", "mixed")
        self.meme_reactions_mode_select.currentIndexChanged.connect(self._on_reaction_mode_changed)
        mode_row.addLayout(mode_copy, 1)
        mode_row.addWidget(self.meme_reactions_mode_select)
        layout.addLayout(mode_row)

        self.meme_choices = self._available_meme_choices()
        self.selected_meme_ids = self._default_meme_ids_for_mode("hand")
        self.meme_selection_status = self._small_label("", "TinyText")
        layout.addWidget(self._small_label("Meme Set", "CardTitleSmall"))
        layout.addWidget(self.meme_selection_status)
        output_row = QHBoxLayout()
        output_row.addWidget(self._small_label("Meme Output Windows", "TinyText"))
        output_row.addStretch()
        self.output_count_input = QSpinBox()
        self.output_count_input.setRange(1, 3)
        self.output_count_input.setValue(1)
        output_row.addWidget(self.output_count_input)
        layout.addLayout(output_row)
        configure = QPushButton("Configure Memes")
        configure.setObjectName("SecondaryButton")
        configure.clicked.connect(self._open_meme_config_dialog)
        add_meme = QPushButton("Add Meme")
        add_meme.setObjectName("SecondaryButton")
        add_meme.clicked.connect(self._open_add_meme_dialog)
        actions = QHBoxLayout()
        actions.addWidget(configure)
        actions.addWidget(add_meme)
        actions.addStretch()
        layout.addLayout(actions)
        self._update_meme_selection_status()
        return panel

    def _available_meme_choices(self) -> list[MemeReaction]:
        engine = MemeReactionEngine.from_config(self.project_root / "configs" / "memes")
        default_ids = {"thumbs_up_cat", "macaco_peace", "macaco_pointing", "absolute_cinema"}

        def sort_key(meme: MemeReaction) -> tuple[int, int, int, str]:
            has_asset = self._meme_asset_exists(meme)
            return (
                0 if meme.id in default_ids else 1,
                0 if has_asset else 1,
                0 if meme.input_type == "hand" else 1,
                meme.name,
            )

        return sorted(engine.memes, key=sort_key)

    def _meme_choice_label(self, meme: MemeReaction) -> str:
        triggers = ", ".join(meme.triggers[:2])
        status = "" if self._meme_asset_exists(meme) else " - asset missing"
        return f"{meme.name} - {triggers} ({meme.input_type}){status}"

    def _meme_asset_exists(self, meme: MemeReaction) -> bool:
        if not meme.asset:
            return False
        asset_path = Path(meme.asset)
        if not asset_path.is_absolute():
            asset_path = self.project_root / asset_path
        return asset_path.exists()

    def _open_meme_config_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Configure Meme Reactions")
        dialog.resize(620, 520)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        mode = self._selected_reaction_mode()
        mode_choices = self._meme_choices_for_mode(mode)
        title = self._small_label(f"Choose up to 5 memes - {self._mode_label(mode)}", "CardTitle")
        status = self._small_label("", "MutedText")
        layout.addWidget(title)
        layout.addWidget(status)
        if mode == "motion":
            hint = self._small_label(
                "Motion precision: one meme per movement trigger. Choosing another with the same trigger replaces the previous one.",
                "TinyText",
            )
            hint.setWordWrap(True)
            layout.addWidget(hint)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(6)

        temp_checkboxes: dict[str, QCheckBox] = {}

        def selected_count() -> int:
            return sum(1 for checkbox in temp_checkboxes.values() if checkbox.isChecked())

        def refresh_status() -> None:
            status.setText(f"Selected memes: {selected_count()}/5")

        def on_choice_changed(item_id: str) -> None:
            checkbox = temp_checkboxes[item_id]
            if checkbox.isChecked() and selected_count() > 5:
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
            refresh_status()

        for meme in mode_choices:
            checkbox = QCheckBox(self._meme_choice_label(meme))
            checkbox.setObjectName("MemeChoice")
            checkbox.setChecked(meme.id in self.selected_meme_ids)
            checkbox.stateChanged.connect(lambda _state, item_id=meme.id: on_choice_changed(item_id))
            temp_checkboxes[meme.id] = checkbox
            content_layout.addWidget(checkbox)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        actions = QHBoxLayout()
        cancel = QPushButton("Cancel")
        save = QPushButton("Save Selection")
        save.setObjectName("PrimaryButton")
        cancel.clicked.connect(dialog.reject)
        save.clicked.connect(dialog.accept)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(save)
        layout.addLayout(actions)
        refresh_status()

        if dialog.exec() == QDialog.Accepted:
            self.selected_meme_ids = {
                item_id
                for item_id, checkbox in temp_checkboxes.items()
                if checkbox.isChecked()
            }
            self._update_meme_selection_status()

    def _open_add_meme_dialog(
        self,
        default_trigger: str | None = None,
        default_input_type: str | None = None,
    ) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Meme")
        dialog.resize(560, 460)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        layout.addWidget(self._small_label("Add Meme To Trigger", "CardTitle"))
        hint = self._small_label(
            "Choose any local GIF/image/audio file. MemeVision copies it into local_assets/ and saves a portable config path.",
            "MutedText",
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Display name, e.g. Scuba Cat")
        trigger_input = QComboBox()
        trigger_input.setEditable(True)
        for trigger in self._known_triggers():
            trigger_input.addItem(trigger)
        trigger_input.setCurrentText(default_trigger or self._default_trigger_for_mode(self._selected_reaction_mode()))

        type_select = QComboBox()
        type_select.addItem("Hand", "hand")
        type_select.addItem("Face", "face")
        type_select.addItem("Motion", "motion")
        mode = default_input_type or self._selected_reaction_mode()
        if mode in {"hand", "face", "motion"}:
            type_select.setCurrentIndex(type_select.findData(mode))

        asset_input = QLineEdit()
        asset_input.setPlaceholderText("local_assets/memes/.../file.gif")
        sound_input = QLineEdit()
        sound_input.setPlaceholderText("optional: local_assets/sounds/.../file.mp3")
        category_input = QLineEdit("reaction")
        cooldown_input = QDoubleSpinBox()
        cooldown_input.setRange(0.1, 30.0)
        cooldown_input.setSingleStep(0.1)
        cooldown_input.setValue(1.0)

        layout.addWidget(self._field_row("Name", name_input))
        layout.addWidget(self._field_row("Trigger", trigger_input))
        layout.addWidget(self._field_row("Type", type_select))
        layout.addWidget(self._path_row("Asset", asset_input, "Meme Assets (*.gif *.png *.jpg *.jpeg *.webp);;All Files (*)"))
        layout.addWidget(self._path_row("Sound", sound_input, "Audio Files (*.mp3 *.wav *.ogg);;All Files (*)"))
        layout.addWidget(self._field_row("Category", category_input))
        layout.addWidget(self._field_row("Cooldown", cooldown_input))

        status = self._small_label("", "TinyText")
        layout.addWidget(status)

        actions = QHBoxLayout()
        cancel = QPushButton("Cancel")
        save = QPushButton("Save Meme")
        save.setObjectName("PrimaryButton")
        cancel.clicked.connect(dialog.reject)

        def save_meme() -> None:
            name = name_input.text().strip()
            trigger = self._normalize_trigger(trigger_input.currentText())
            asset = asset_input.text().strip()
            sound = sound_input.text().strip()
            input_type = str(type_select.currentData())
            if not name or not trigger or not asset:
                status.setText("Name, trigger, and asset are required.")
                return
            asset_path = Path(asset)
            if not asset_path.is_absolute():
                asset_path = self.project_root / asset_path
            if not asset_path.exists():
                status.setText("Asset file does not exist.")
                return
            sound_path = None
            if sound:
                sound_path = Path(sound)
                if not sound_path.is_absolute():
                    sound_path = self.project_root / sound_path
                if not sound_path.exists():
                    status.setText("Sound file does not exist.")
                    return

            meme_id = self._unique_meme_id(self._slugify(name))
            asset = self._prepare_local_media(asset_path, input_type, "memes", meme_id)
            sound = (
                self._prepare_local_media(sound_path, input_type, "sounds", meme_id)
                if sound_path is not None
                else None
            )
            entry = {
                "id": meme_id,
                "name": name,
                "asset": asset,
                "sound": sound,
                "input_type": input_type,
                "cooldown_seconds": cooldown_input.value(),
                "category": category_input.text().strip() or "reaction",
            }
            self._append_meme_entry(trigger, entry)
            self._reload_meme_choices(select_meme_id=meme_id)
            self._add_timeline_event(f"Added meme: {name} -> {trigger}")
            dialog.accept()

        save.clicked.connect(save_meme)
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(save)
        layout.addLayout(actions)
        dialog.exec()

    def _on_reaction_mode_changed(self, *_args) -> None:
        mode = self._selected_reaction_mode()
        valid_ids = {meme.id for meme in self._meme_choices_for_mode(mode)}
        self.selected_meme_ids = {item_id for item_id in self.selected_meme_ids if item_id in valid_ids}
        if not self.selected_meme_ids:
            self.selected_meme_ids = self._default_meme_ids_for_mode(mode)
        self._update_meme_selection_status()

    def _meme_choices_for_mode(self, mode: str) -> list[MemeReaction]:
        if mode == "mixed":
            return self.meme_choices
        return [meme for meme in self.meme_choices if meme.input_type == mode]

    def _default_meme_ids_for_mode(self, mode: str) -> set[str]:
        defaults_by_mode = {
            "hand": {"thumbs_up_cat", "macaco_peace", "macaco_pointing", "absolute_cinema"},
            "face": {"bruh", "surprised_pikachu", "side_eye_dog", "npc_wojak"},
            "motion": {"cat_nope", "tung_sahur_67", "scuba_fox"},
            "mixed": {"thumbs_up_cat", "macaco_peace", "bruh", "cat_nope", "scuba_fox"},
        }
        preferred = defaults_by_mode.get(mode, set())
        choices = self._meme_choices_for_mode(mode)
        selected = {meme.id for meme in choices if meme.id in preferred}
        if selected:
            return selected
        return {meme.id for meme in choices[: min(4, len(choices))]}

    def _mode_label(self, mode: str) -> str:
        labels = {
            "hand": "Hands",
            "face": "Face",
            "motion": "Motion",
            "mixed": "Mixed",
        }
        return labels.get(mode, mode.title())

    def _meme_by_id(self, item_id: str) -> MemeReaction | None:
        return next((meme for meme in self.meme_choices if meme.id == item_id), None)

    def _build_session_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(44, 36, 44, 36)
        layout.setSpacing(16)
        layout.addWidget(self._page_header(
            "Session Console",
            "Runtime controls and event log. The camera and meme output run in separate windows.",
        ))

        controls = QFrame()
        controls.setObjectName("PanelCard")
        controls_layout = QVBoxLayout(controls)
        controls_layout.setContentsMargins(18, 18, 18, 18)
        controls_layout.setSpacing(10)
        self.live_status = self._small_label("No project launched", "MutedText")
        self.live_plugin = self._small_label("Plugin: none", "MetricText")
        controls_layout.addWidget(self._small_label("Active Session", "CardTitle"))
        controls_layout.addWidget(self.live_status)
        controls_layout.addWidget(self.live_plugin)

        metrics = [
            ("Camera", "Not started"),
            ("Hands", "Not loaded"),
            ("Gesture", "Waiting"),
            ("Face", "Waiting"),
            ("FPS", "--"),
            ("Meme", "None"),
        ]
        for name, value in metrics:
            controls_layout.addWidget(self._metric_row(name, value))

        self.debug_landmarks_toggle = QCheckBox("Debug Landmarks")
        self.debug_landmarks_toggle.setObjectName("DebugToggle")
        self.debug_landmarks_toggle.stateChanged.connect(self._on_debug_landmarks_changed)
        controls_layout.addWidget(self.debug_landmarks_toggle)

        camera_row = QHBoxLayout()
        camera_row.addWidget(self._small_label("Camera Index", "TinyText"))
        camera_row.addStretch()
        self.camera_index_input = QSpinBox()
        self.camera_index_input.setRange(0, 9)
        self.camera_index_input.setValue(0)
        camera_row.addWidget(self.camera_index_input)
        controls_layout.addLayout(camera_row)

        meme_size_row = QHBoxLayout()
        meme_size_row.addWidget(self._small_label("Meme Size", "TinyText"))
        self.meme_size_value = self._small_label("100%", "MetricText")
        self.meme_size_slider = QSlider(Qt.Horizontal)
        self.meme_size_slider.setObjectName("MemeSizeSlider")
        self.meme_size_slider.setRange(25, 160)
        self.meme_size_slider.setValue(100)
        self.meme_size_slider.valueChanged.connect(self._on_meme_size_changed)
        meme_size_row.addWidget(self.meme_size_slider, 1)
        meme_size_row.addWidget(self.meme_size_value)
        controls_layout.addLayout(meme_size_row)

        buttons = QHBoxLayout()
        stop = QPushButton("Stop Session")
        stop.clicked.connect(self._stop_session)
        screenshot = QPushButton("Screenshot Camera")
        screenshot.clicked.connect(self._save_screenshot)
        buttons.addWidget(stop)
        buttons.addWidget(screenshot)
        buttons.addStretch()
        controls_layout.addLayout(buttons)
        layout.addWidget(controls)

        log = QFrame()
        log.setObjectName("PanelCard")
        log_layout = QVBoxLayout(log)
        log_layout.setContentsMargins(18, 18, 18, 18)
        log_layout.addWidget(self._small_label("Event Log", "CardTitle"))
        self.timeline_label = self._small_label("No events yet.", "MutedText")
        self.timeline_label.setWordWrap(True)
        log_layout.addWidget(self.timeline_label)
        layout.addWidget(log)
        layout.addStretch()
        return page

    def _build_gesture_recorder_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(44, 36, 44, 36)
        layout.setSpacing(16)
        layout.addWidget(self._page_header(
            "Gesture Recorder",
            "Record three-second motion landmark samples that can become reusable no-code gesture profiles.",
        ))

        panel = QFrame()
        panel.setObjectName("PanelCard")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(12)
        panel_layout.addWidget(self._small_label("Record Motion Sample", "CardTitle"))
        instructions = self._small_label(
            "Start a recorder camera session, enter a snake_case id, press record, wait for 3 2 1 on the camera window, and perform the movement for 3 seconds.",
            "MutedText",
        )
        instructions.setWordWrap(True)
        panel_layout.addWidget(instructions)

        self.motion_gesture_id_input = QLineEdit("my_motion_gesture")
        self.motion_gesture_id_input.setPlaceholderText("snake_case id, e.g. arm_wave_side")
        panel_layout.addWidget(self._field_row("Gesture ID", self.motion_gesture_id_input))

        self.start_motion_session_button = QPushButton("Start Motion Session")
        self.start_motion_session_button.setObjectName("SecondaryButton")
        self.start_motion_session_button.clicked.connect(self._start_motion_session_for_recorder)
        self.stop_recorder_camera_button = QPushButton("Stop Camera")
        self.stop_recorder_camera_button.setObjectName("SecondaryButton")
        self.stop_recorder_camera_button.clicked.connect(self._stop_recorder_camera)
        self.record_motion_button = QPushButton("Record Motion Sample")
        self.record_motion_button.setObjectName("PrimaryButton")
        self.record_motion_button.clicked.connect(self._start_motion_recording_countdown)
        self.attach_meme_button = QPushButton("Attach Meme To This Gesture")
        self.attach_meme_button.setObjectName("SecondaryButton")
        self.attach_meme_button.clicked.connect(self._attach_meme_to_recorded_gesture)
        actions = QHBoxLayout()
        actions.addWidget(self.start_motion_session_button)
        actions.addWidget(self.stop_recorder_camera_button)
        actions.addWidget(self.record_motion_button)
        actions.addWidget(self.attach_meme_button)
        actions.addStretch()
        panel_layout.addLayout(actions)

        self.recorder_status_label = self._small_label(
            "Status: start the recorder camera before recording.",
            "MutedText",
        )
        self.recorder_status_label.setWordWrap(True)
        panel_layout.addWidget(self.recorder_status_label)
        layout.addWidget(panel)

        saved_panel = QFrame()
        saved_panel.setObjectName("PanelCard")
        saved_layout = QVBoxLayout(saved_panel)
        saved_layout.setContentsMargins(18, 18, 18, 18)
        saved_layout.setSpacing(8)
        saved_layout.addWidget(self._small_label("Saved Location", "CardTitle"))
        saved_layout.addWidget(self._small_label("configs/gestures/motion/<gesture_id>.json", "CodeText"))
        note = self._small_label(
            "After recording, link the same Gesture ID to a Motion meme in Add Meme, then restart a Motion session to use it.",
            "TinyText",
        )
        note.setWordWrap(True)
        saved_layout.addWidget(note)
        layout.addWidget(saved_panel)
        layout.addStretch()
        return page

    def _launch_project(
        self,
        plugin: PluginManifest,
        after_page_index: int = 2,
        minimize_after_launch: bool = True,
    ) -> None:
        if plugin.id != "meme_reactions":
            self._add_timeline_event(f"Concept selected: {plugin.name}")
            self.stack.setCurrentIndex(2)
            return

        reaction_mode = self._selected_reaction_mode()
        selected_meme_ids = self._selected_meme_ids()
        if not selected_meme_ids:
            self._add_timeline_event("Launch blocked: select at least one meme first")
            self.stack.setCurrentIndex(1)
            return

        self._stop_session()
        self._open_code_editor(self.project_root)
        self.camera_window = StreamWindow("MemeVision Camera", "Starting camera...")
        output_count = self._selected_output_count()
        self.meme_windows = [
            StreamWindow(f"MemeVision Meme Output {index + 1}", "Waiting for gesture...")
            for index in range(output_count)
        ]
        self.meme_window = self.meme_windows[0]
        self.camera_window.move(120, 120)
        for index, meme_window in enumerate(self.meme_windows):
            meme_window.move(900 + (index * 46), 120 + (index * 46))
        self.camera_window.show()
        for meme_window in self.meme_windows:
            meme_window.show()
        QTimer.singleShot(900, self._present_stream_windows)

        camera_index = self.camera_index_input.value()
        self.camera_worker = CameraWorker(
            camera_index=camera_index,
            project_root=self.project_root,
            parent=self,
        )
        self.camera_worker.debug_landmarks = self.debug_landmarks_toggle.isChecked()
        self.camera_worker.reaction_mode = reaction_mode
        self.camera_worker.allowed_meme_ids = selected_meme_ids
        self.camera_worker.output_window_count = output_count
        self.camera_worker.frame_ready.connect(self._on_camera_frame)
        self.camera_worker.face_ready.connect(self._on_face_result)
        self.camera_worker.meme_frame_ready.connect(self._on_meme_frame)
        self.camera_worker.meme_cleared.connect(self._on_meme_cleared)
        self.camera_worker.error.connect(self._on_camera_error)
        self.camera_worker.tracking_status.connect(self._on_tracking_status)
        self.camera_worker.tracking_sample_ready.connect(self._on_tracking_sample_ready)
        self.camera_worker.meme_triggered.connect(self._on_meme_triggered)
        self.camera_worker.stopped.connect(self._on_camera_stopped)
        self.camera_worker.start()
        self._on_meme_size_changed(self.meme_size_slider.value())

        self.live_status.setText("Running in separate Camera and Meme Output windows")
        self.live_plugin.setText(f"Plugin: {plugin.name}")
        self._set_metric("Camera", f"Starting {camera_index}")
        self._add_timeline_event(
            f"Launched {plugin.name} in {reaction_mode} mode with {len(selected_meme_ids)} memes and {output_count} outputs"
        )
        self.stack.setCurrentIndex(after_page_index)
        if minimize_after_launch:
            self.showMinimized()

    def _start_motion_session_for_recorder(self) -> None:
        self._stop_session()
        self.camera_window = StreamWindow("MemeVision Gesture Recorder Camera", "Starting camera...")
        self.camera_window.move(120, 120)
        self.camera_window.show()
        QTimer.singleShot(500, self.camera_window.present_above_others)

        camera_index = self.camera_index_input.value()
        self.camera_worker = CameraWorker(
            camera_index=camera_index,
            project_root=self.project_root,
            parent=self,
        )
        self.camera_worker.debug_landmarks = True
        self.camera_worker.reaction_mode = "motion"
        self.camera_worker.allowed_meme_ids = set()
        self.camera_worker.output_window_count = 0
        self.camera_worker.frame_ready.connect(self._on_camera_frame)
        self.camera_worker.face_ready.connect(self._on_face_result)
        self.camera_worker.error.connect(self._on_camera_error)
        self.camera_worker.tracking_status.connect(self._on_tracking_status)
        self.camera_worker.tracking_sample_ready.connect(self._on_tracking_sample_ready)
        self.camera_worker.stopped.connect(self._on_camera_stopped)
        self.camera_worker.start()
        self.live_status.setText("Gesture Recorder camera session running")
        self.live_plugin.setText("Plugin: Gesture Recorder")
        self._set_metric("Camera", f"Starting {camera_index}")
        self._set_recorder_status("Status: camera-only recorder session started. Press Record Motion Sample when ready.")
        self._add_timeline_event("Started Gesture Recorder camera session")

    def _stop_recorder_camera(self) -> None:
        self._stop_session()
        self._set_recorder_status("Status: recorder camera stopped.")
        self._add_timeline_event("Stopped Gesture Recorder camera session")

    def _attach_meme_to_recorded_gesture(self) -> None:
        gesture_id = self._normalize_trigger(self.motion_gesture_id_input.text() if self.motion_gesture_id_input else "")
        if not gesture_id:
            self._set_recorder_status("Status: enter a gesture id before attaching a meme.")
            return
        self._open_add_meme_dialog(default_trigger=gesture_id, default_input_type="motion")

    def _present_stream_windows(self) -> None:
        if self.camera_window is not None:
            self.camera_window.present_above_others()
        if self.meme_window is not None:
            for meme_window in self.meme_windows:
                meme_window.present_above_others()

    def _open_code_editor(self, project_path: Path) -> None:
        code = shutil.which("code") or shutil.which("code.cmd")
        if code is None:
            self._add_timeline_event("VS Code command not found. Open the folder manually if needed.")
            return
        try:
            subprocess.Popen([code, str(project_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._add_timeline_event(f"Opened VS Code: {project_path.name}")
        except OSError as error:
            self._add_timeline_event(f"Could not open VS Code: {error}")

    def _stop_session(self) -> None:
        if self.camera_worker is not None and self.camera_worker.isRunning():
            self.camera_worker.stop()
            self.camera_worker.wait(1500)
        self.camera_worker = None
        self.last_frame_image = None
        if self.camera_window is not None:
            self.camera_window.close()
            self.camera_window = None
        for meme_window in self.meme_windows:
            meme_window.close()
        self.meme_windows = []
        self.meme_window = None
        if hasattr(self, "metric_values"):
            self._set_metric("Camera", "Stopped")
            self._set_metric("FPS", "--")
            self._set_metric("Hands", "Not loaded")
            self._set_metric("Gesture", "Waiting")
            self._set_metric("Meme", "None")
        self.recording_deadline = None
        self.gesture_recorder = None
        if self.record_motion_button is not None:
            self.record_motion_button.setEnabled(True)

    def _on_camera_frame(self, frame, fps: float, hand_result) -> None:
        if self.camera_window is not None:
            self.camera_window.set_frame(frame)
        self.last_frame_image = self._image_from_frame(frame)
        self._set_metric("Camera", "Live")
        self._set_metric("FPS", f"{fps:.1f}")
        if hand_result.available:
            self._set_metric("Hands", str(hand_result.hands_count))
            self._set_metric("Gesture", hand_result.gesture)

    def _on_face_result(self, face_result) -> None:
        self._set_metric("Face", f"{face_result.faces_count} - {face_result.expression}")

    def _on_meme_frame(self, frame, meme_name: str, slot_index: int) -> None:
        if 0 <= slot_index < len(self.meme_windows):
            self.meme_windows[slot_index].set_frame(frame)
        self._set_metric("Meme", meme_name)

    def _on_meme_cleared(self) -> None:
        for meme_window in self.meme_windows:
            meme_window.set_message("Waiting for gesture...")
        self._set_metric("Meme", "None")

    def _on_camera_error(self, message: str) -> None:
        if self.camera_window is not None:
            self.camera_window.set_message(message)
        self._set_metric("Camera", "Error")
        self._add_timeline_event(message)

    def _on_tracking_status(self, message: str) -> None:
        lowered = message.lower()
        if "face" in lowered and "ready" in lowered:
            self._set_metric("Face", "Ready")
        elif "hand" in lowered and "ready" in lowered:
            self._set_metric("Hands", "Ready")
        else:
            if "face" in lowered:
                self._set_metric("Face", "Unavailable")
            elif "hand" in lowered or "mediapipe" in lowered:
                self._set_metric("Hands", "Unavailable")
        self._add_timeline_event(message)

    def _on_meme_triggered(self, meme_name: str, sound_path: str) -> None:
        self._set_metric("Meme", meme_name)
        self._add_timeline_event(f"Meme triggered: {meme_name}")
        self._play_meme_sound(sound_path)

    def _on_camera_stopped(self) -> None:
        self._set_metric("Camera", "Stopped")

    def _start_motion_recording_countdown(self) -> None:
        if self.camera_worker is None or not self.camera_worker.isRunning():
            self._set_recorder_status("Status: start the recorder camera first.")
            self._add_timeline_event("Gesture recording requires the recorder camera")
            return
        if self.camera_worker.reaction_mode not in {"motion", "mixed"}:
            self._set_recorder_status("Status: recorder camera must run in Motion mode.")
            self._add_timeline_event("Gesture recording skipped: recorder camera is not in Motion mode")
            return
        gesture_id = self._normalize_trigger(self.motion_gesture_id_input.text() if self.motion_gesture_id_input else "")
        if not gesture_id:
            self._set_recorder_status("Status: enter a gesture id first.")
            self._add_timeline_event("Gesture recording skipped: enter a gesture id")
            return
        self.gesture_recorder = GestureSampleRecorder(gesture_id=gesture_id, kind="motion")
        self.record_countdown_remaining = 3
        if self.record_motion_button is not None:
            self.record_motion_button.setEnabled(False)
        self._set_recorder_status("Status: countdown started. Get ready.")
        self._run_recording_countdown()

    def _run_recording_countdown(self) -> None:
        if self.record_countdown_remaining > 0:
            self._set_recorder_status(f"Status: recording starts in {self.record_countdown_remaining}.")
            if self.camera_window is not None:
                self.camera_window.set_overlay_message(str(self.record_countdown_remaining))
            self._add_timeline_event(f"Gesture recording starts in {self.record_countdown_remaining}")
            self.record_countdown_remaining -= 1
            QTimer.singleShot(1000, self._run_recording_countdown)
            return
        self.recording_deadline = 0.0
        if self.camera_window is not None:
            self.camera_window.set_overlay_message("REC")
        self._set_recorder_status("Status: recording for 3 seconds. Perform the gesture now.")
        self._add_timeline_event("Recording motion sample for 3 seconds")

    def _on_tracking_sample_ready(
        self,
        now: float,
        hand_result: HandTrackingResult,
        face_result: FaceTrackingResult,
        detected_gesture: str,
    ) -> None:
        if self.gesture_recorder is None or self.recording_deadline is None:
            return
        if self.recording_deadline == 0.0:
            self.recording_deadline = now + self.recording_duration_seconds
        if now <= self.recording_deadline:
            self.gesture_recorder.add_sample(now, hand_result, face_result, detected_gesture)
            return
        self._finish_motion_recording()

    def _finish_motion_recording(self) -> None:
        if self.gesture_recorder is None:
            return
        sample_count = len(self.gesture_recorder.samples)
        output_path = self.gesture_recorder.save(self.project_root)
        self._set_recorder_status(
            f"Status: saved {output_path.name} with {sample_count} samples. Restart the session to use it."
        )
        self._add_timeline_event(f"Saved gesture sample: {output_path.name} ({sample_count} samples)")
        self.gesture_recorder = None
        self.recording_deadline = None
        if self.camera_window is not None:
            self.camera_window.set_overlay_message("Saved")
            QTimer.singleShot(1200, lambda: self.camera_window.set_overlay_message("") if self.camera_window else None)
        if self.record_motion_button is not None:
            self.record_motion_button.setEnabled(True)

    def _set_recorder_status(self, message: str) -> None:
        if self.recorder_status_label is not None:
            self.recorder_status_label.setText(message)

    def _save_screenshot(self) -> None:
        if self.last_frame_image is None:
            self._add_timeline_event("Screenshot skipped: camera is not live")
            return
        captures_dir = self.project_root / "captures"
        captures_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = captures_dir / f"memevision-{timestamp}.png"
        if self.last_frame_image.save(str(path)):
            self._add_timeline_event(f"Screenshot saved: {path.name}")
        else:
            self._add_timeline_event("Screenshot failed: image could not be saved")

    def _image_from_frame(self, frame) -> QImage:
        image_format = QImage.Format_RGBA8888 if frame.shape[2] == 4 else QImage.Format_RGB888
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        return QImage(frame.data, width, height, bytes_per_line, image_format).copy()

    def _on_debug_landmarks_changed(self, *_args) -> None:
        if self.camera_worker is not None:
            self.camera_worker.debug_landmarks = self.debug_landmarks_toggle.isChecked()
        state = "on" if self.debug_landmarks_toggle.isChecked() else "off"
        self._add_timeline_event(f"Debug landmarks {state}")

    def _on_meme_size_changed(self, value: int) -> None:
        self.meme_size_value.setText(f"{value}%")
        if self.meme_window is not None:
            for meme_window in self.meme_windows:
                meme_window.set_frame_scale(value / 100)

    def _field_row(self, label: str, field: QWidget) -> QWidget:
        row = QFrame()
        row.setObjectName("FieldRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._small_label(label, "TinyText"))
        layout.addWidget(field, 1)
        return row

    def _path_row(self, label: str, field: QLineEdit, file_filter: str) -> QWidget:
        row = QFrame()
        row.setObjectName("FieldRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        browse = QPushButton("Browse")
        browse.setObjectName("SecondaryButton")

        def browse_file() -> None:
            file_path, _selected_filter = QFileDialog.getOpenFileName(
                self,
                f"Select {label}",
                str(self.project_root / "local_assets"),
                file_filter,
            )
            if file_path:
                field.setText(self._project_relative_path(Path(file_path)))

        browse.clicked.connect(browse_file)
        layout.addWidget(self._small_label(label, "TinyText"))
        layout.addWidget(field, 1)
        layout.addWidget(browse)
        return row

    def _known_triggers(self) -> list[str]:
        triggers = {trigger for meme in self.meme_choices for trigger in meme.triggers}
        triggers.update(self._recorded_gesture_triggers())
        return sorted(triggers)

    def _recorded_gesture_triggers(self) -> set[str]:
        triggers: set[str] = set()
        gestures_dir = self.project_root / "configs" / "gestures"
        for config_path in gestures_dir.glob("*/*.json"):
            gesture_id = config_path.stem
            try:
                payload = json.loads(config_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                payload = {}
            if isinstance(payload, dict):
                gesture_id = str(payload.get("gesture_id") or gesture_id)
            normalized = self._normalize_trigger(gesture_id)
            if normalized:
                triggers.add(normalized)
        return triggers

    def _default_trigger_for_mode(self, mode: str) -> str:
        defaults = {
            "hand": "thumbs_up",
            "face": "open_mouth",
            "motion": "scuba_wave_side",
            "mixed": "thumbs_up",
        }
        return defaults.get(mode, "thumbs_up")

    def _normalize_trigger(self, value: str) -> str:
        return self._slugify(value).replace("-", "_")

    def _slugify(self, value: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
        return slug or "meme"

    def _unique_meme_id(self, base_id: str) -> str:
        existing_ids = {meme.id for meme in self.meme_choices}
        candidate = base_id
        suffix = 2
        while candidate in existing_ids:
            candidate = f"{base_id}_{suffix}"
            suffix += 1
        return candidate

    def _project_relative_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.project_root.resolve()).as_posix()
        except ValueError:
            return str(path)

    def _prepare_local_media(
        self,
        source_path: Path,
        input_type: str,
        media_kind: str,
        base_name: str,
    ) -> str:
        source_path = source_path.resolve()
        local_root = (self.project_root / "local_assets").resolve()
        try:
            source_path.relative_to(local_root)
            return self._project_relative_path(source_path)
        except ValueError:
            pass

        type_folder = {
            "hand": "hands",
            "face": "face",
            "motion": "motion",
        }.get(input_type, input_type)
        destination_dir = self.project_root / "local_assets" / media_kind / type_folder
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = self._unique_media_destination(destination_dir, base_name, source_path.suffix)
        shutil.copy2(source_path, destination)
        return self._project_relative_path(destination)

    def _unique_media_destination(self, destination_dir: Path, base_name: str, suffix: str) -> Path:
        safe_base = self._slugify(base_name)
        normalized_suffix = suffix.lower() or ".bin"
        candidate = destination_dir / f"{safe_base}{normalized_suffix}"
        index = 2
        while candidate.exists():
            candidate = destination_dir / f"{safe_base}_{index}{normalized_suffix}"
            index += 1
        return candidate

    def _append_meme_entry(self, trigger: str, entry: dict[str, object]) -> None:
        config_dir = self.project_root / "configs" / "memes" / "by_trigger"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / f"{trigger}.json"
        entries = []
        if config_path.exists():
            entries = json.loads(config_path.read_text(encoding="utf-8"))
        entries.append(entry)
        config_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _reload_meme_choices(self, select_meme_id: str | None = None) -> None:
        self.meme_choices = self._available_meme_choices()
        valid_ids = {meme.id for meme in self._meme_choices_for_mode(self._selected_reaction_mode())}
        self.selected_meme_ids = {item_id for item_id in self.selected_meme_ids if item_id in valid_ids}
        if select_meme_id in valid_ids:
            self.selected_meme_ids.add(select_meme_id)
        if len(self.selected_meme_ids) > 5:
            self.selected_meme_ids = set(sorted(self.selected_meme_ids)[:5])
        if not self.selected_meme_ids:
            self.selected_meme_ids = self._default_meme_ids_for_mode(self._selected_reaction_mode())
        self._update_meme_selection_status()

    def _selected_meme_ids(self) -> set[str]:
        return set(self.selected_meme_ids)

    def _selected_reaction_mode(self) -> str:
        if self.meme_reactions_mode_select is None:
            return "hand"
        return str(self.meme_reactions_mode_select.currentData())

    def _selected_output_count(self) -> int:
        if self.output_count_input is None:
            return 1
        return self.output_count_input.value()

    def _update_meme_selection_status(self) -> None:
        if self.meme_selection_status is not None:
            selected_count = len(self._selected_meme_ids())
            names = [
                f"{meme.name} ({meme.triggers[0]})"
                for meme in self.meme_choices
                if meme.id in self.selected_meme_ids and meme.triggers
            ]
            preview = ", ".join(names[:3])
            if len(names) > 3:
                preview += f" +{len(names) - 3} more"
            if not preview:
                preview = "None selected"
            mode = self._mode_label(self._selected_reaction_mode())
            total_for_mode = len(self._meme_choices_for_mode(self._selected_reaction_mode()))
            self.meme_selection_status.setText(
                f"{mode}: {selected_count}/5 selected from {total_for_mode} - {preview}"
            )

    def _play_meme_sound(self, sound_path: str) -> None:
        if not sound_path:
            return
        path = Path(sound_path)
        if not path.is_absolute():
            path = self.project_root / path
        if not path.exists():
            return
        try:
            import pygame
            if not self.audio_ready:
                pygame.mixer.init()
                self.audio_ready = True
            pygame.mixer.Sound(str(path)).play()
        except Exception as error:
            self._add_timeline_event(f"Audio skipped: {error}")

    def _capability_grid(self) -> QWidget:
        wrapper = QWidget()
        layout = QGridLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        cards = [
            ("Launchable", "Runs like a desktop workshop, not a script."),
            ("Code-first", "Opens VS Code so students inspect the source."),
            ("Separate Windows", "Camera and meme output are independent."),
            ("Plugins", "Each project can grow as its own experiment."),
        ]
        for index, (title, text) in enumerate(cards):
            layout.addWidget(self._info_card(title, text), index // 2, index % 2)
        return wrapper

    def _info_card(self, title: str, text: str) -> QWidget:
        card = QFrame()
        card.setObjectName("InfoCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(self._small_label(title, "CardTitle"))
        description = self._small_label(text, "MutedText")
        description.setWordWrap(True)
        layout.addWidget(description)
        return card

    def _metric_row(self, name: str, value: str) -> QWidget:
        row = QFrame()
        row.setObjectName("MetricRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.addWidget(self._small_label(name, "TinyText"))
        layout.addStretch()
        val = self._small_label(value, "MetricText")
        self.metric_values[name] = val
        layout.addWidget(val)
        return row

    def _sorted_plugins(self) -> list[PluginManifest]:
        return sorted(self.plugins, key=lambda item: (0 if item.id == "meme_reactions" else 1, item.category, item.name))

    def _page_header(self, title: str, subtitle: str) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._small_label(title, "AppTitle"))
        description = self._small_label(subtitle, "Subtitle")
        description.setWordWrap(True)
        layout.addWidget(description)
        return wrapper

    def _small_label(self, text: str, object_name: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def _set_metric(self, name: str, value: str) -> None:
        label = self.metric_values.get(name)
        if label is not None:
            label.setText(value)

    def _add_timeline_event(self, message: str) -> None:
        if not hasattr(self, "timeline_label"):
            return
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.timeline_label.setText(f"[{timestamp}] {message}")

    def _launch_first_plugin(self) -> None:
        plugin = next((item for item in self.plugins if item.id == "meme_reactions"), None)
        if plugin is not None:
            self._launch_project(plugin)
        else:
            self.stack.setCurrentIndex(1)
