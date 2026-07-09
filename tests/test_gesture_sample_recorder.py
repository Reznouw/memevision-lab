from __future__ import annotations

import json

from memevision_lab.core.face_tracker import FaceTrackingResult
from memevision_lab.core.gesture_sample_recorder import GestureSampleRecorder
from memevision_lab.core.hand_tracker import HandState, HandTrackingResult


def test_motion_sample_recorder_writes_landmark_json(tmp_path):
    recorder = GestureSampleRecorder("my_wave", kind="motion")
    hand_result = HandTrackingResult(
        True,
        1,
        "open_palm",
        0.8,
        palm_x=0.25,
        palm_y=0.4,
        hands=(HandState("open_palm", 0.8, 0.25, 0.4),),
    )
    face_result = FaceTrackingResult(True, 1, "neutral_face", 0.7, nose_x=0.5, nose_y=0.3)

    recorder.add_sample(10.0, hand_result, face_result, "open_palm")
    recorder.add_sample(10.5, hand_result, face_result, "open_palm")
    output_path = recorder.save(tmp_path)

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path == tmp_path / "configs" / "gestures" / "motion" / "my_wave.json"
    assert payload["gesture_id"] == "my_wave"
    assert payload["kind"] == "motion"
    assert payload["sample_count"] == 2
    assert payload["duration_seconds"] == 0.5
    assert payload["samples"][0]["hands"][0] == {
        "x": 0.25,
        "y": 0.4,
        "gesture": "open_palm",
        "confidence": 0.8,
    }
    assert payload["samples"][0]["face"]["expression"] == "neutral_face"


def test_motion_sample_recorder_handles_no_face_result():
    recorder = GestureSampleRecorder("hand_only", kind="motion")
    hand_result = HandTrackingResult(True, 0, "none", 0.0)
    face_result = FaceTrackingResult(False, 0, "unavailable", 0.0)

    recorder.add_sample(1.0, hand_result, face_result, "none")

    assert recorder.to_payload()["samples"][0]["face"] is None
