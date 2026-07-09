from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class HandGestureResult:
    gesture: str
    confidence: float
    extended_fingers: tuple[str, ...]


class GestureEngine:
    finger_names = ("thumb", "index", "middle", "ring", "pinky")

    def classify_hand(self, landmarks: list[tuple[float, float, float]], handedness: str) -> HandGestureResult:
        if len(landmarks) < 21:
            return HandGestureResult("unknown", 0.0, ())

        extended = self._extended_fingers(landmarks, handedness)
        extended_set = set(extended)

        long_fingers = extended_set.intersection({"index", "middle", "ring", "pinky"})

        if {"index", "middle"}.issubset(extended_set) and not {"ring", "pinky"}.intersection(extended_set):
            return HandGestureResult("peace", 0.88, extended)
        if "index" in extended_set and not {"middle", "ring", "pinky"}.intersection(extended_set):
            return HandGestureResult("pointing", 0.82, extended)
        if "thumb" in extended_set and not long_fingers:
            return HandGestureResult("thumbs_up", 0.78, extended)
        if self._looks_like_fist(landmarks, extended_set):
            return HandGestureResult("fist", 0.86, extended)
        if len(long_fingers) >= 4:
            return HandGestureResult("open_palm", 0.84, extended)
        if not extended_set:
            return HandGestureResult("fist", 0.8, extended)

        return HandGestureResult("hand_detected", 0.55, extended)

    def _extended_fingers(
        self,
        landmarks: list[tuple[float, float, float]],
        handedness: str,
    ) -> tuple[str, ...]:
        extended: list[str] = []

        # Thumb is horizontal in MediaPipe's 2D hand model. Direction depends on handedness.
        thumb_tip_x = landmarks[4][0]
        thumb_ip_x = landmarks[3][0]
        thumb_tip_distance = self._distance(landmarks[4], landmarks[2])
        thumb_ip_distance = self._distance(landmarks[3], landmarks[2])
        if handedness.lower() == "right":
            if thumb_tip_x < thumb_ip_x and thumb_tip_distance > thumb_ip_distance * 1.04:
                extended.append("thumb")
        elif thumb_tip_x > thumb_ip_x and thumb_tip_distance > thumb_ip_distance * 1.04:
            extended.append("thumb")

        for name, tip_index, pip_index in (
            ("index", 8, 6),
            ("middle", 12, 10),
            ("ring", 16, 14),
            ("pinky", 20, 18),
        ):
            tip = landmarks[tip_index]
            pip = landmarks[pip_index]
            mcp = landmarks[pip_index - 1]
            tip_farther_from_wrist = self._distance(tip, landmarks[0]) > self._distance(pip, landmarks[0]) * 1.08
            tip_above_joint = tip[1] < pip[1]
            tip_farther_from_mcp = self._distance(tip, mcp) > self._distance(pip, mcp) * 1.05
            if tip_above_joint and tip_farther_from_wrist and tip_farther_from_mcp:
                extended.append(name)

        return tuple(extended)

    def _looks_like_fist(
        self,
        landmarks: list[tuple[float, float, float]],
        extended_set: set[str],
    ) -> bool:
        long_extended = extended_set.intersection({"index", "middle", "ring", "pinky"})
        if len(long_extended) > 1:
            return False

        folded_count = 0
        for tip_index, pip_index in ((8, 6), (12, 10), (16, 14), (20, 18)):
            tip = landmarks[tip_index]
            pip = landmarks[pip_index]
            wrist = landmarks[0]
            if self._distance(tip, wrist) <= self._distance(pip, wrist) * 1.12:
                folded_count += 1
        return folded_count >= 3

    def _distance(self, a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
        return math.hypot(a[0] - b[0], a[1] - b[1])
