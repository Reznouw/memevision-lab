from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FaceTrackingResult:
    available: bool
    faces_count: int
    expression: str
    confidence: float
    message: str = ""
    nose_x: float | None = None
    nose_y: float | None = None


class FaceTracker:
    def __init__(self, max_num_faces: int = 1) -> None:
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
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=max_num_faces,
            refine_landmarks=True,
            min_detection_confidence=0.55,
            min_tracking_confidence=0.5,
        )
        self.drawing_utils = mp.solutions.drawing_utils
        self.drawing_styles = mp.solutions.drawing_styles

    def process(self, rgb_frame: Any, draw_landmarks: bool = False) -> tuple[Any, FaceTrackingResult]:
        results = self.face_mesh.process(rgb_frame)
        if not results.multi_face_landmarks:
            return rgb_frame, FaceTrackingResult(True, 0, "none", 0.0)

        face_landmarks = results.multi_face_landmarks[0]
        points = [(point.x, point.y, point.z) for point in face_landmarks.landmark]
        expression, confidence = self._classify(points)

        if draw_landmarks:
            self.drawing_utils.draw_landmarks(
                image=rgb_frame,
                landmark_list=face_landmarks,
                connections=self.mp.solutions.face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=self.drawing_styles.get_default_face_mesh_contours_style(),
            )

        return rgb_frame, FaceTrackingResult(
            True,
            len(results.multi_face_landmarks),
            expression,
            confidence,
            nose_x=points[1][0],
            nose_y=points[1][1],
        )

    def close(self) -> None:
        self.face_mesh.close()

    def _classify(self, points: list[tuple[float, float, float]]) -> tuple[str, float]:
        if len(points) < 468:
            return "unknown", 0.0

        face_width = max(abs(points[234][0] - points[454][0]), 0.001)
        face_height = max(abs(points[10][1] - points[152][1]), 0.001)

        mouth_open = abs(points[13][1] - points[14][1]) / face_height
        left_eye_open = abs(points[159][1] - points[145][1]) / face_height
        right_eye_open = abs(points[386][1] - points[374][1]) / face_height
        nose_offset = (points[1][0] - ((points[234][0] + points[454][0]) / 2)) / face_width

        if mouth_open > 0.055:
            return "open_mouth", 0.82
        if left_eye_open < 0.012 and right_eye_open < 0.012:
            return "closed_eyes", 0.78
        if abs(nose_offset) > 0.12:
            return "look_side", 0.72
        if mouth_open < 0.025 and left_eye_open > 0.014 and right_eye_open > 0.014:
            return "neutral_face", 0.68
        return "face_detected", 0.55
