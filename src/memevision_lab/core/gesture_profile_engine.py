from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MotionGestureProfile:
    gesture_id: str
    hand_count: int
    axis: str
    range_x: float
    range_y: float
    direction_changes: int


class GestureProfileEngine:
    def __init__(self, profiles: list[MotionGestureProfile]) -> None:
        self.profiles = profiles

    @classmethod
    def from_config(cls, config_path: Path) -> GestureProfileEngine:
        if not config_path.exists():
            return cls([])
        profiles = []
        for file_path in sorted(config_path.glob("*.json")):
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            profile = cls._profile_from_payload(payload, fallback_id=file_path.stem)
            if profile is not None:
                profiles.append(profile)
        return cls(profiles)

    @classmethod
    def _profile_from_payload(
        cls,
        payload: dict[str, Any],
        fallback_id: str,
    ) -> MotionGestureProfile | None:
        samples = payload.get("samples") or []
        hand_frames = [sample.get("hands") or [] for sample in samples]
        hand_counts = [len(hands) for hands in hand_frames]
        usable_frames = [hands for hands in hand_frames if hands]
        if len(usable_frames) < 4:
            return None

        hand_count = 2 if sum(1 for count in hand_counts if count >= 2) >= len(samples) / 2 else 1
        xs, ys = cls._motion_series(usable_frames, hand_count)
        range_x = cls._range(xs)
        range_y = cls._range(ys)
        axis = "x" if range_x >= range_y else "y"
        direction_changes = cls._direction_changes(xs if axis == "x" else ys)
        if max(range_x, range_y) < 0.025:
            return None
        return MotionGestureProfile(
            gesture_id=str(payload.get("gesture_id") or fallback_id),
            hand_count=hand_count,
            axis=axis,
            range_x=round(range_x, 5),
            range_y=round(range_y, 5),
            direction_changes=direction_changes,
        )

    def match(
        self,
        hand_points: list[tuple[float, float, float, str]],
        multi_hand_points: list[tuple[float, tuple[tuple[float, float, str], ...]]],
    ) -> str | None:
        for profile in self.profiles:
            if self._matches_profile(profile, hand_points, multi_hand_points):
                return profile.gesture_id
        return None

    def _matches_profile(
        self,
        profile: MotionGestureProfile,
        hand_points: list[tuple[float, float, float, str]],
        multi_hand_points: list[tuple[float, tuple[tuple[float, float, str], ...]]],
    ) -> bool:
        if profile.hand_count >= 2:
            frames = [frame[1] for frame in multi_hand_points if len(frame[1]) >= 2]
            if len(frames) < 4:
                return False
            xs, ys = self._motion_series([list(frame) for frame in frames], 2)
        else:
            if len(hand_points) < 4:
                return False
            xs = [point[1] for point in hand_points]
            ys = [point[2] for point in hand_points]

        range_x = self._range(xs)
        range_y = self._range(ys)
        if profile.axis == "x":
            movement_ok = range_x >= profile.range_x * 0.65 and range_x >= range_y * 0.7
            changes = self._direction_changes(xs)
        else:
            movement_ok = range_y >= profile.range_y * 0.65 and range_y >= range_x * 0.7
            changes = self._direction_changes(ys)
        changes_ok = changes >= max(0, profile.direction_changes - 1)
        return movement_ok and changes_ok

    @staticmethod
    def _motion_series(
        hand_frames: list[list[dict[str, Any]] | tuple[tuple[float, float, str], ...]],
        hand_count: int,
    ) -> tuple[list[float], list[float]]:
        xs: list[float] = []
        ys: list[float] = []
        for hands in hand_frames:
            if hand_count >= 2 and len(hands) >= 2:
                points = [_as_xy(hand) for hand in hands[:2]]
                xs.append(sum(point[0] for point in points) / 2)
                ys.append(sum(point[1] for point in points) / 2)
            elif hands:
                x, y = _as_xy(hands[0])
                xs.append(x)
                ys.append(y)
        return xs, ys

    @staticmethod
    def _range(values: list[float]) -> float:
        if not values:
            return 0.0
        return max(values) - min(values)

    @staticmethod
    def _direction_changes(values: list[float]) -> int:
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


def _as_xy(hand: dict[str, Any] | tuple[float, float, str]) -> tuple[float, float]:
    if isinstance(hand, dict):
        return float(hand["x"]), float(hand["y"])
    return float(hand[0]), float(hand[1])
