from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memevision_lab.core.face_tracker import FaceTrackingResult
from memevision_lab.core.hand_tracker import HandTrackingResult


@dataclass
class GestureSampleRecorder:
    gesture_id: str
    kind: str = "motion"
    started_at: float | None = None
    samples: list[dict[str, Any]] = field(default_factory=list)

    def add_sample(
        self,
        now: float,
        hand_result: HandTrackingResult,
        face_result: FaceTrackingResult,
        detected_gesture: str,
    ) -> None:
        if self.started_at is None:
            self.started_at = now
        self.samples.append(
            {
                "t": round(now - self.started_at, 4),
                "detected_gesture": detected_gesture,
                "hands": [
                    {
                        "x": round(hand.palm_x, 5),
                        "y": round(hand.palm_y, 5),
                        "gesture": hand.gesture,
                        "confidence": round(hand.confidence, 4),
                    }
                    for hand in hand_result.hands
                ],
                "face": {
                    "x": round(face_result.nose_x, 5) if face_result.nose_x is not None else None,
                    "y": round(face_result.nose_y, 5) if face_result.nose_y is not None else None,
                    "expression": face_result.expression,
                    "confidence": round(face_result.confidence, 4),
                }
                if face_result.available
                else None,
            }
        )

    def to_payload(self) -> dict[str, Any]:
        duration = self.samples[-1]["t"] if self.samples else 0.0
        return {
            "schema_version": 1,
            "gesture_id": self.gesture_id,
            "kind": self.kind,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": duration,
            "sample_count": len(self.samples),
            "samples": self.samples,
        }

    def save(self, project_root: Path) -> Path:
        output_dir = project_root / "configs" / "gestures" / self.kind
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.gesture_id}.json"
        output_path.write_text(
            json.dumps(self.to_payload(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return output_path
