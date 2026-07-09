from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from memevision_lab.core.face_tracker import FaceTracker, FaceTrackingResult
from memevision_lab.core.hand_tracker import HandTracker, HandTrackingResult
from memevision_lab.core.meme_assets import MemeAssetCache
from memevision_lab.core.meme_reactions import MemeReactionEngine
from memevision_lab.core.motion_gesture_engine import MotionGestureEngine


class CameraWorker(QThread):
    frame_ready = Signal(object, float, object)
    face_ready = Signal(object)
    meme_frame_ready = Signal(object, str, int)
    meme_cleared = Signal()
    error = Signal(str)
    tracking_status = Signal(str)
    meme_triggered = Signal(str, str)
    stopped = Signal()

    def __init__(self, camera_index: int = 0, project_root: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.camera_index = camera_index
        self.project_root = project_root if project_root is not None else self._discover_default_project_root()
        self._running = False
        self.debug_landmarks = False
        self.reaction_mode = "hand"
        self.allowed_meme_ids: set[str] | None = None
        self.output_window_count = 1

    def run(self) -> None:
        try:
            import cv2
        except ImportError:
            self.error.emit(
                "OpenCV is not installed. Run: python -m pip install opencv-python numpy"
            )
            self.stopped.emit()
            return

        capture = cv2.VideoCapture(self.camera_index)
        if not capture.isOpened():
            self.error.emit(f"Could not open camera index {self.camera_index}.")
            self.stopped.emit()
            return

        self._running = True
        last_time = time.perf_counter()
        fps = 0.0
        hand_tracker = None
        face_tracker = None
        hand_tracking_attempted = False
        face_tracking_attempted = False
        frame_count = 0
        reaction_engine = MemeReactionEngine.from_config(self.project_root / "configs" / "memes")
        reaction_engine.active_input_type = self.reaction_mode
        reaction_engine.allowed_meme_ids = self.allowed_meme_ids
        asset_cache = MemeAssetCache(self.project_root)
        motion_engine = MotionGestureEngine()
        last_emitted_reaction_id = ""
        last_valid_gesture_at = time.monotonic()
        last_valid_gesture = "none"
        clear_delay_seconds = 0.25

        while self._running:
            ok, frame = capture.read()
            if not ok:
                self.error.emit("Camera frame could not be read.")
                break

            now = time.perf_counter()
            elapsed = now - last_time
            last_time = now
            if elapsed > 0:
                fps = 0.85 * fps + 0.15 * (1.0 / elapsed) if fps else 1.0 / elapsed

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            hand_result = HandTrackingResult(False, 0, "unavailable", 0.0)
            face_result = FaceTrackingResult(False, 0, "unavailable", 0.0)

            if self.reaction_mode in {"hand", "motion", "mixed"} and not hand_tracking_attempted and frame_count >= 5:
                hand_tracking_attempted = True
                self.tracking_status.emit("Loading MediaPipe hand tracking")
                hand_tracker = self._create_hand_tracker()

            if self.reaction_mode in {"face", "motion", "mixed"} and not face_tracking_attempted and frame_count >= 5:
                face_tracking_attempted = True
                self.tracking_status.emit("Loading MediaPipe face tracking")
                face_tracker = self._create_face_tracker()

            if hand_tracker is not None:
                frame, hand_result = hand_tracker.process(frame, draw_landmarks=self.debug_landmarks)
            if face_tracker is not None:
                frame, face_result = face_tracker.process(frame, draw_landmarks=self.debug_landmarks)

            motion_result = motion_engine.update(now, hand_result, face_result)
            detected_gesture = self._select_reaction_signal(hand_result, face_result, motion_result.gesture)

            if detected_gesture not in {"none", "unknown", "unavailable", "hand_detected", "face_detected"}:
                last_valid_gesture_at = now
                last_valid_gesture = detected_gesture

            gesture_for_reaction = detected_gesture
            if now - last_valid_gesture_at <= clear_delay_seconds and gesture_for_reaction in {
                "none",
                "unknown",
                "unavailable",
                "hand_detected",
                "face_detected",
            }:
                gesture_for_reaction = last_valid_gesture

            reactions = reaction_engine.update_many(gesture_for_reaction, self.output_window_count)
            if reactions:
                emitted_ids = []
                for slot_index, reaction in enumerate(reactions[: self.output_window_count]):
                    asset_frame = asset_cache.frame_for(reaction.meme.asset)
                    if asset_frame is not None:
                        self.meme_frame_ready.emit(asset_frame, reaction.name, slot_index)
                    emitted_ids.append(reaction.meme.id)
                    if reaction.meme.id not in last_emitted_reaction_id.split("|"):
                        self.meme_triggered.emit(reaction.name, reaction.meme.sound)
                last_emitted_reaction_id = "|".join(emitted_ids)
            else:
                if last_emitted_reaction_id:
                    self.meme_cleared.emit()
                last_emitted_reaction_id = ""

            self.frame_ready.emit(frame, fps, hand_result)
            if face_result.available:
                self.face_ready.emit(face_result)
            frame_count += 1
            self.msleep(1)

        capture.release()
        if hand_tracker is not None:
            hand_tracker.close()
        if face_tracker is not None:
            face_tracker.close()
        self.stopped.emit()

    def stop(self) -> None:
        self._running = False

    def _create_hand_tracker(self) -> HandTracker | None:
        try:
            hand_tracker = HandTracker()
            self.tracking_status.emit("MediaPipe hand tracking ready")
            return hand_tracker
        except Exception as error:
            self.tracking_status.emit(str(error))
            return None

    def _create_face_tracker(self) -> FaceTracker | None:
        try:
            face_tracker = FaceTracker()
            self.tracking_status.emit("MediaPipe face tracking ready")
            return face_tracker
        except Exception as error:
            self.tracking_status.emit(str(error))
            return None

    def _select_reaction_signal(
        self,
        hand_result: HandTrackingResult,
        face_result: FaceTrackingResult,
        motion_gesture: str,
    ) -> str:
        if self.reaction_mode == "hand":
            return hand_result.gesture
        if self.reaction_mode == "face":
            return face_result.expression
        if self.reaction_mode == "motion":
            return motion_gesture
        if motion_gesture not in {"none", "unknown", "unavailable"}:
            return motion_gesture
        if hand_result.gesture not in {"none", "unknown", "unavailable", "hand_detected"}:
            return hand_result.gesture
        return face_result.expression

    def _discover_default_project_root(self) -> Path:
        for parent in Path(__file__).resolve().parents:
            if (parent / "plugins").exists() or (parent / "configs").exists():
                return parent
        return Path.cwd()
