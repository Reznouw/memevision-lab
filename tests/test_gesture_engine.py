from __future__ import annotations

from memevision_lab.core.gesture_engine import GestureEngine


def test_closed_fingers_vertical_palm_counts_as_open_palm():
    result = GestureEngine().classify_hand(_vertical_palm_landmarks(), "right")

    assert result.gesture == "open_palm"
    assert set(result.extended_fingers).issuperset({"index", "middle", "ring", "pinky"})


def test_folded_fingers_still_count_as_fist():
    result = GestureEngine().classify_hand(_fist_landmarks(), "right")

    assert result.gesture == "fist"


def _vertical_palm_landmarks() -> list[tuple[float, float, float]]:
    landmarks = [(0.5, 0.9, 0.0)] * 21
    landmarks[1] = (0.42, 0.82, 0.0)
    landmarks[2] = (0.38, 0.76, 0.0)
    landmarks[3] = (0.36, 0.70, 0.0)
    landmarks[4] = (0.34, 0.66, 0.0)
    _set_finger(landmarks, 5, 6, 8, 0.47)
    _set_finger(landmarks, 9, 10, 12, 0.50)
    _set_finger(landmarks, 13, 14, 16, 0.53)
    _set_finger(landmarks, 17, 18, 20, 0.56)
    return landmarks


def _fist_landmarks() -> list[tuple[float, float, float]]:
    landmarks = [(0.5, 0.9, 0.0)] * 21
    for mcp, pip, tip, x in ((5, 6, 8, 0.45), (9, 10, 12, 0.50), (13, 14, 16, 0.55), (17, 18, 20, 0.60)):
        landmarks[mcp] = (x, 0.68, 0.0)
        landmarks[pip] = (x, 0.58, 0.0)
        landmarks[tip] = (x, 0.78, 0.0)
    return landmarks


def _set_finger(
    landmarks: list[tuple[float, float, float]],
    mcp: int,
    pip: int,
    tip: int,
    x: float,
) -> None:
    landmarks[mcp] = (x, 0.66, 0.0)
    landmarks[pip] = (x, 0.46, 0.0)
    landmarks[tip] = (x, 0.24, 0.0)
    landmarks[pip + 1] = (x, 0.35, 0.0)
