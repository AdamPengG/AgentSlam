from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CameraIntrinsics:
    fx: float
    fy: float
    cx: float
    cy: float


@dataclass(frozen=True)
class Pose2D:
    x: float
    y: float
    yaw: float
    z: float = 0.0


@dataclass(frozen=True)
class SemanticDetection:
    label: str
    pixel_x: float
    pixel_y: float
    depth_m: float
    confidence: float = 1.0


@dataclass(frozen=True)
class FrameObservation:
    frame_id: str
    pose: Pose2D
    intrinsics: CameraIntrinsics
    detections: list[SemanticDetection]


@dataclass
class SemanticObject:
    object_id: str
    label: str
    x: float
    y: float
    z: float
    observation_count: int = 1
    confidence_sum: float = 1.0
    frames: list[str] = field(default_factory=list)

    def update(self, x: float, y: float, z: float, confidence: float, frame_id: str) -> None:
        total = self.observation_count + 1
        self.x = ((self.x * self.observation_count) + x) / total
        self.y = ((self.y * self.observation_count) + y) / total
        self.z = ((self.z * self.observation_count) + z) / total
        self.observation_count = total
        self.confidence_sum += confidence
        if frame_id not in self.frames:
            self.frames.append(frame_id)

    @property
    def mean_confidence(self) -> float:
        return self.confidence_sum / max(self.observation_count, 1)
