from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import rclpy
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo
from std_msgs.msg import String

from semantic_mapper_pkg.models import CameraIntrinsics, Pose2D
from semantic_mapper_pkg.runtime import parse_detection_envelope

from .geometry import GeometricMapBuilder


class LocalizedGeometricMapperNode(Node):
    """Create a small occupancy-style 2D map from localized detection rays."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("agentslam_localized_geometric_mapper")
        self.args = args
        self.builder = GeometricMapBuilder(resolution_m=args.resolution_m)
        self.output_path = Path(args.output)
        self.latest_intrinsics: CameraIntrinsics | None = None
        self.latest_pose: Pose2D | None = None
        self.last_frame_time: float | None = None
        self.finalized = False
        self.pending_detection_payloads: list[str] = []

        self.metrics = {
            "frames_processed": 0,
            "camera_info_messages": 0,
            "pose_messages": 0,
            "detection_messages": 0,
            "skipped_detection_messages": 0,
            "buffered_detection_messages": 0,
        }

        self.create_subscription(CameraInfo, args.camera_info_topic, self._on_camera_info, 10)
        self.create_subscription(Odometry, args.pose_topic, self._on_pose, 10)
        self.create_subscription(String, args.detections_topic, self._on_detections, 10)
        self.create_timer(0.5, self._check_idle_timeout)

    def _on_camera_info(self, msg: CameraInfo) -> None:
        self.metrics["camera_info_messages"] += 1
        self.latest_intrinsics = CameraIntrinsics(
            fx=float(msg.k[0]),
            fy=float(msg.k[4]),
            cx=float(msg.k[2]),
            cy=float(msg.k[5]),
        )
        self._drain_pending_detections()

    def _on_pose(self, msg: Odometry) -> None:
        self.metrics["pose_messages"] += 1
        self.latest_pose = Pose2D(
            x=float(msg.pose.pose.position.x),
            y=float(msg.pose.pose.position.y),
            z=float(msg.pose.pose.position.z),
            yaw=quaternion_to_yaw(
                msg.pose.pose.orientation.x,
                msg.pose.pose.orientation.y,
                msg.pose.pose.orientation.z,
                msg.pose.pose.orientation.w,
            ),
        )
        self._drain_pending_detections()

    def _on_detections(self, msg: String) -> None:
        self.metrics["detection_messages"] += 1
        if self.latest_intrinsics is None or self.latest_pose is None:
            self.metrics["buffered_detection_messages"] += 1
            self.pending_detection_payloads.append(msg.data)
            return
        self._process_detection_payload(msg.data)

    def _drain_pending_detections(self) -> None:
        if self.latest_intrinsics is None or self.latest_pose is None:
            return
        while self.pending_detection_payloads:
            self._process_detection_payload(self.pending_detection_payloads.pop(0))

    def _process_detection_payload(self, payload: str) -> None:
        if self.latest_intrinsics is None or self.latest_pose is None:
            self.metrics["skipped_detection_messages"] += 1
            return

        envelope = parse_detection_envelope(payload)
        self.builder.add_observation(
            frame_id=envelope.frame_id,
            pose=self.latest_pose,
            intrinsics=self.latest_intrinsics,
            detections=envelope.detections,
        )
        self.metrics["frames_processed"] += 1
        self.last_frame_time = time.monotonic()

        if self.args.expected_frames and self.metrics["frames_processed"] >= self.args.expected_frames:
            self.finalize(reason="expected_frames_reached")

    def _check_idle_timeout(self) -> None:
        if self.finalized:
            return
        if self.metrics["frames_processed"] == 0 or self.last_frame_time is None:
            return
        if (time.monotonic() - self.last_frame_time) >= self.args.idle_timeout:
            self.finalize(reason="idle_timeout")

    def finalize(self, *, reason: str) -> None:
        if self.finalized:
            return
        self.finalized = True
        self.metrics["skipped_detection_messages"] += len(self.pending_detection_payloads)
        self.pending_detection_payloads.clear()
        self.builder.export_to_path(self.output_path)
        runtime_path = self.output_path.with_name(f"{self.output_path.stem}_runtime.json")
        runtime_payload = {
            **self.metrics,
            "finalize_reason": reason,
            "output_path": str(self.output_path),
            "resolution_m": self.args.resolution_m,
            "pose_topic": self.args.pose_topic,
        }
        runtime_path.write_text(json.dumps(runtime_payload, indent=2), encoding="utf-8")


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a localized 2D occupancy-style map from replay/live detection rays."
    )
    parser.add_argument("--output", required=True, help="Output path for the localized geometric map JSON.")
    parser.add_argument("--resolution-m", type=float, default=0.25, help="Grid resolution in meters.")
    parser.add_argument("--expected-frames", type=int, default=0, help="Finalize after this many frames if >0.")
    parser.add_argument("--idle-timeout", type=float, default=3.0, help="Finalize after this much idle time.")
    parser.add_argument("--camera-info-topic", default="/agentslam/camera/rgb/camera_info")
    parser.add_argument("--pose-topic", default="/agentslam/localization/odom")
    parser.add_argument("--detections-topic", default="/agentslam/semantic_detections")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rclpy.init(args=None)
    node = LocalizedGeometricMapperNode(args)
    try:
        while rclpy.ok() and not node.finalized:
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        if not node.finalized:
            node.finalize(reason="external_shutdown")
    except KeyboardInterrupt:
        if not node.finalized:
            node.finalize(reason="keyboard_interrupt")
    finally:
        if not node.finalized:
            node.finalize(reason="shutdown")
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
