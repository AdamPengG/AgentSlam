from __future__ import annotations

import json
from pathlib import Path

from .models import CameraIntrinsics, FrameObservation, Pose2D, SemanticDetection


def load_fixture(path: str | Path) -> list[FrameObservation]:
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    intrinsics = CameraIntrinsics(**payload["intrinsics"])
    frames: list[FrameObservation] = []
    for frame_payload in payload["frames"]:
        pose = Pose2D(**frame_payload["pose"])
        detections = [
            SemanticDetection(
                label=item["label"],
                pixel_x=item["pixel_x"],
                pixel_y=item["pixel_y"],
                depth_m=item["depth_m"],
                confidence=item.get("confidence", 1.0),
            )
            for item in frame_payload["detections"]
        ]
        frames.append(
            FrameObservation(
                frame_id=frame_payload["frame_id"],
                pose=pose,
                intrinsics=intrinsics,
                detections=detections,
            )
        )
    return frames
