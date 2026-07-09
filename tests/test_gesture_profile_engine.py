from __future__ import annotations

import json

from memevision_lab.core.face_tracker import FaceTrackingResult
from memevision_lab.core.gesture_profile_engine import GestureProfileEngine
from memevision_lab.core.hand_tracker import HandState, HandTrackingResult
from memevision_lab.core.motion_gesture_engine import MotionGestureEngine


def test_loads_motion_profile_from_recorded_sample(tmp_path):
    config_dir = tmp_path / "configs" / "gestures" / "motion"
    config_dir.mkdir(parents=True)
    (config_dir / "my_wave.json").write_text(json.dumps(_motion_payload("my_wave")), encoding="utf-8")

    engine = GestureProfileEngine.from_config(config_dir)

    assert len(engine.profiles) == 1
    assert engine.profiles[0].gesture_id == "my_wave"
    assert engine.profiles[0].axis == "x"


def test_motion_engine_matches_recorded_profile(tmp_path):
    config_dir = tmp_path / "configs" / "gestures" / "motion"
    config_dir.mkdir(parents=True)
    (config_dir / "my_wave.json").write_text(json.dumps(_motion_payload("my_wave")), encoding="utf-8")
    engine = MotionGestureEngine(window_seconds=2.0, profile_path=config_dir)
    face_result = FaceTrackingResult(False, 0, "unavailable", 0.0)

    result = None
    for index, x in enumerate((0.2, 0.3, 0.42, 0.32, 0.22, 0.35)):
        result = engine.update(
            float(index) / 10,
            HandTrackingResult(
                True,
                1,
                "open_palm",
                0.8,
                palm_x=x,
                palm_y=0.4,
                hands=(HandState("open_palm", 0.8, x, 0.4),),
            ),
            face_result,
        )

    assert result is not None
    assert result.gesture == "my_wave"


def test_ignores_too_small_recorded_motion(tmp_path):
    config_dir = tmp_path / "configs" / "gestures" / "motion"
    config_dir.mkdir(parents=True)
    payload = _motion_payload("tiny")
    for sample in payload["samples"]:
        sample["hands"][0]["x"] = 0.2
    (config_dir / "tiny.json").write_text(json.dumps(payload), encoding="utf-8")

    engine = GestureProfileEngine.from_config(config_dir)

    assert engine.profiles == []


def _motion_payload(gesture_id: str):
    xs = (0.2, 0.3, 0.42, 0.32, 0.22, 0.35)
    return {
        "schema_version": 1,
        "gesture_id": gesture_id,
        "kind": "motion",
        "duration_seconds": 1.0,
        "sample_count": len(xs),
        "samples": [
            {
                "t": index / 10,
                "detected_gesture": "open_palm",
                "hands": [
                    {
                        "x": x,
                        "y": 0.4,
                        "gesture": "open_palm",
                        "confidence": 0.8,
                    }
                ],
                "face": None,
            }
            for index, x in enumerate(xs)
        ],
    }
