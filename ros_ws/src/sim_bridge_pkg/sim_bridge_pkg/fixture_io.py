from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BridgeIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class BridgePose:
    x: float
    y: float
    yaw: float
    z: float = 0.0


@dataclass(frozen=True)
class BridgeDetection:
    label: str
    pixel_x: float
    pixel_y: float
    depth_m: float
    confidence: float


@dataclass(frozen=True)
class BridgeFrame:
    frame_id: str
    pose: BridgePose
    detections: list[BridgeDetection]


@dataclass(frozen=True)
class BridgeFixture:
    intrinsics: BridgeIntrinsics
    frames: list[BridgeFrame]


def load_bridge_fixture(path: str | Path) -> BridgeFixture:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    intrinsics = BridgeIntrinsics(**payload["intrinsics"])

    frames = []
    for frame_payload in payload["frames"]:
        detections = [
            BridgeDetection(
                label=item["label"],
                pixel_x=item["pixel_x"],
                pixel_y=item["pixel_y"],
                depth_m=item["depth_m"],
                confidence=item.get("confidence", 1.0),
            )
            for item in frame_payload["detections"]
        ]
        frames.append(
            BridgeFrame(
                frame_id=frame_payload["frame_id"],
                pose=BridgePose(**frame_payload["pose"]),
                detections=detections,
            )
        )
    return BridgeFixture(intrinsics=intrinsics, frames=frames)


def quaternion_from_yaw(yaw: float) -> tuple[float, float, float, float]:
    half_yaw = yaw * 0.5
    return (0.0, 0.0, math.sin(half_yaw), math.cos(half_yaw))
