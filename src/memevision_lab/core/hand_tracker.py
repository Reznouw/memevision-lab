from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memevision_lab.core.gesture_engine import GestureEngine


@dataclass(frozen=True)
class HandState:
    gesture: str
    confidence: float
    palm_x: float
    palm_y: float


@dataclass(frozen=True)
class HandTrackingResult:
    available: bool
    hands_count: int
    gesture: str
    confidence: float
    message: str = ""
    palm_x: float | None = None
    palm_y: float | None = None
    hands: tuple[HandState, ...] = ()


class HandTracker:
    def __init__(self, max_num_hands: int = 2) -> None:
        try:
            import mediapipe as mp
        except ImportError as error:
            raise RuntimeError(
                "MediaPipe is not installed. Use Python 3.11/3.12 and run: "
                "python -m pip install -e .[vision]"
            ) from error

        if not hasattr(mp, "solutions"):
            raise RuntimeError(
                "Installed MediaPipe does not expose the classic solutions API. "
                "Run: python -m pip install 'mediapipe>=0.10.21,<0.10.35'"
            )

        self.mp = mp
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.55,
        )
        self.drawing_utils = mp.solutions.drawing_utils
        self.drawing_styles = mp.solutions.drawing_styles
        self.gesture_engine = GestureEngine()

    def process(self, rgb_frame: Any, draw_landmarks: bool = False) -> tuple[Any, HandTrackingResult]:
        results = self.hands.process(rgb_frame)
        if not results.multi_hand_landmarks:
            return rgb_frame, HandTrackingResult(True, 0, "none", 0.0)

        best_gesture = "hand_detected"
        best_confidence = 0.0
        best_palm_x = None
        best_palm_y = None
        hand_states: list[HandState] = []
        hands_count = len(results.multi_hand_landmarks)

        for index, hand_landmarks in enumerate(results.multi_hand_landmarks):
            handedness = "unknown"
            if results.multi_handedness and index < len(results.multi_handedness):
                handedness = results.multi_handedness[index].classification[0].label

            landmarks = [(point.x, point.y, point.z) for point in hand_landmarks.landmark]
            gesture = self.gesture_engine.classify_hand(landmarks, handedness)
            palm_x, palm_y = self._palm_center(landmarks)
            hand_states.append(HandState(gesture.gesture, gesture.confidence, palm_x, palm_y))
            if gesture.confidence > best_confidence:
                best_gesture = gesture.gesture
                best_confidence = gesture.confidence
                best_palm_x, best_palm_y = palm_x, palm_y

            if draw_landmarks:
                self.drawing_utils.draw_landmarks(
                    rgb_frame,
                    hand_landmarks,
                    self.mp.solutions.hands.HAND_CONNECTIONS,
                    self.drawing_styles.get_default_hand_landmarks_style(),
                    self.drawing_styles.get_default_hand_connections_style(),
                )

        return rgb_frame, HandTrackingResult(
            True,
            hands_count,
            best_gesture,
            best_confidence,
            palm_x=best_palm_x,
            palm_y=best_palm_y,
            hands=tuple(hand_states),
        )

    def close(self) -> None:
        self.hands.close()

    def _palm_center(self, landmarks: list[tuple[float, float, float]]) -> tuple[float, float]:
        palm_points = [landmarks[index] for index in (0, 5, 9, 13, 17)]
        x = sum(point[0] for point in palm_points) / len(palm_points)
        y = sum(point[1] for point in palm_points) / len(palm_points)
        return x, y
