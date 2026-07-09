from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from memevision_lab.core.face_tracker import FaceTrackingResult
from memevision_lab.core.hand_tracker import HandTrackingResult


@dataclass(frozen=True)
class MotionGestureResult:
    gesture: str
    confidence: float


class MotionGestureEngine:
    def __init__(self, window_seconds: float = 1.15) -> None:
        self.window_seconds = window_seconds
        self.hand_points: deque[tuple[float, float, float, str]] = deque()
        self.multi_hand_points: deque[tuple[float, tuple[tuple[float, float, str], ...]]] = deque()
        self.face_points: deque[tuple[float, float, float]] = deque()

    def update(
        self,
        now: float,
        hand_result: HandTrackingResult,
        face_result: FaceTrackingResult,
    ) -> MotionGestureResult:
        if hand_result.available and hand_result.palm_x is not None and hand_result.palm_y is not None:
            self.hand_points.append((now, hand_result.palm_x, hand_result.palm_y, hand_result.gesture))
        if hand_result.available and hand_result.hands:
            self.multi_hand_points.append(
                (now, tuple((hand.palm_x, hand.palm_y, hand.gesture) for hand in hand_result.hands))
            )
        if face_result.available and face_result.nose_x is not None and face_result.nose_y is not None:
            self.face_points.append((now, face_result.nose_x, face_result.nose_y))

        self._trim(now)

        if self._is_head_shake():
            return MotionGestureResult("head_shake", 0.82)
        if self._is_scuba_wave_side():
            return MotionGestureResult("scuba_wave_side", 0.86)
        if self._is_two_hand_palm_bounce():
            return MotionGestureResult("two_hand_palm_bounce", 0.84)
        if self._is_palm_bounce():
            return MotionGestureResult("palm_bounce", 0.8)
        if self._is_hand_wave_side():
            return MotionGestureResult("hand_wave_side", 0.78)
        return MotionGestureResult("none", 0.0)

    def _trim(self, now: float) -> None:
        while self.hand_points and now - self.hand_points[0][0] > self.window_seconds:
            self.hand_points.popleft()
        while self.multi_hand_points and now - self.multi_hand_points[0][0] > self.window_seconds:
            self.multi_hand_points.popleft()
        while self.face_points and now - self.face_points[0][0] > self.window_seconds:
            self.face_points.popleft()

    def _is_head_shake(self) -> bool:
        if len(self.face_points) < 6:
            return False
        xs = [point[1] for point in self.face_points]
        return max(xs) - min(xs) > 0.055 and self._direction_changes(xs) >= 2

    def _is_palm_bounce(self) -> bool:
        if len(self.hand_points) < 6:
            return False
        open_palm_count = sum(1 for point in self.hand_points if point[3] == "open_palm")
        if open_palm_count < max(3, len(self.hand_points) // 2):
            return False
        ys = [point[2] for point in self.hand_points]
        return max(ys) - min(ys) > 0.08 and self._direction_changes(ys) >= 2

    def _is_two_hand_palm_bounce(self) -> bool:
        if len(self.multi_hand_points) < 4:
            return False

        two_hand_frames = [frame for frame in self.multi_hand_points if len(frame[1]) >= 2]
        if len(two_hand_frames) < 3:
            return False

        left, right = self._two_hand_series(two_hand_frames)
        left_xs, left_ys = [point[0] for point in left], [point[1] for point in left]
        right_xs, right_ys = [point[0] for point in right], [point[1] for point in right]
        left_vertical = self._range(left_ys)
        right_vertical = self._range(right_ys)
        left_horizontal = self._range(left_xs)
        right_horizontal = self._range(right_xs)
        y_difference = [left_y - right_y for left_y, right_y in zip(left_ys, right_ys)]
        average_y = [(left_y + right_y) / 2 for left_y, right_y in zip(left_ys, right_ys)]

        vertical_sum = left_vertical + right_vertical
        horizontal_sum = left_horizontal + right_horizontal
        separation_changes = self._range(y_difference)

        alternating = separation_changes > 0.045 and (left_vertical > 0.025 or right_vertical > 0.025)
        together = self._range(average_y) > 0.032 and self._direction_changes(average_y) >= 1
        strong_two_hand_vertical = vertical_sum > 0.065 and separation_changes > 0.035
        mostly_vertical = vertical_sum > horizontal_sum * 0.35
        return mostly_vertical and (alternating or together or strong_two_hand_vertical)

    def _is_scuba_wave_side(self) -> bool:
        if len(self.multi_hand_points) < 6:
            return False

        two_hand_frames = [frame for frame in self.multi_hand_points if len(frame[1]) >= 2]
        if len(two_hand_frames) < 5:
            return False

        left, right = self._two_hand_series(two_hand_frames)
        candidates = ((left, right), (right, left))
        latest_nose = self.face_points[-1][1:] if self.face_points else None

        for moving, anchor in candidates:
            moving_xs = [point[0] for point in moving]
            moving_ys = [point[1] for point in moving]
            anchor_xs = [point[0] for point in anchor]
            anchor_ys = [point[1] for point in anchor]
            moving_horizontal = self._range(moving_xs)
            moving_vertical = self._range(moving_ys)
            anchor_stability = self._range(anchor_xs) + self._range(anchor_ys)
            anchor_latest = anchor[-1]
            anchor_near_face = True
            if latest_nose is not None:
                anchor_near_face = self._distance_2d(anchor_latest, latest_nose) < 0.24

            if (
                anchor_near_face
                and anchor_stability < 0.16
                and moving_horizontal > 0.075
                and moving_horizontal > moving_vertical * 1.15
                and self._direction_changes(moving_xs) >= 1
            ):
                return True
        return False

    def _is_hand_wave_side(self) -> bool:
        if len(self.hand_points) < 6:
            return False
        if self._has_two_hands_recent():
            return False
        xs = [point[1] for point in self.hand_points]
        ys = [point[2] for point in self.hand_points]
        horizontal_range = max(xs) - min(xs)
        vertical_range = max(ys) - min(ys)
        return horizontal_range > 0.10 and horizontal_range > vertical_range * 1.25 and self._direction_changes(xs) >= 2

    def _has_two_hands_recent(self) -> bool:
        recent_two_hands = [frame for frame in self.multi_hand_points if len(frame[1]) >= 2]
        return len(recent_two_hands) >= 4

    def _two_hand_series(
        self,
        frames: list[tuple[float, tuple[tuple[float, float, str], ...]]],
    ) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        left: list[tuple[float, float]] = []
        right: list[tuple[float, float]] = []
        for _timestamp, hands in frames:
            sorted_hands = sorted(hands, key=lambda hand: hand[0])[:2]
            left.append((sorted_hands[0][0], sorted_hands[0][1]))
            right.append((sorted_hands[1][0], sorted_hands[1][1]))
        return left, right

    def _range(self, values: list[float]) -> float:
        if not values:
            return 0.0
        return max(values) - min(values)

    def _distance_2d(self, a: tuple[float, float], b: tuple[float, float]) -> float:
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

    def _direction_changes(self, values: list[float]) -> int:
        changes = 0
        previous_direction = 0
        for before, after in zip(values, values[1:]):
            delta = after - before
            if abs(delta) < 0.01:
                continue
            direction = 1 if delta > 0 else -1
            if previous_direction and direction != previous_direction:
                changes += 1
            previous_direction = direction
        return changes
