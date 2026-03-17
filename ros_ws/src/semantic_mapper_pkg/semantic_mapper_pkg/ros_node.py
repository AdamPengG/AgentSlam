from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image, Imu
from std_msgs.msg import String

from .cli import build_map_from_fixture
from .models import CameraIntrinsics, Pose2D
from .map_builder import SemanticMapBuilder
from .runtime import build_frame_observation, export_query_results, parse_detection_envelope


class SemanticMapperNode(Node):
    """Minimal Phase 1 mapper that fuses ROS topics into exported map artifacts."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("semantic_mapper_phase1")
        self.args = args
        self.builder = SemanticMapBuilder(merge_distance_m=args.merge_distance)
        self.output_path = Path(args.output)
        self.query_output_dir = Path(args.query_output_dir)
        self.query_labels = args.query_label
        self.expected_frames = args.expected_frames
        self.idle_timeout_s = args.idle_timeout

        self.latest_intrinsics: CameraIntrinsics | None = None
        self.latest_pose: Pose2D | None = None
        self.latest_pose_frame_id = ""
        self.last_frame_time: float | None = None
        self.finalized = False
        self.pending_detection_payloads: list[str] = []

        self.metrics = {
            "mode": args.mode,
            "frames_processed": 0,
            "skipped_detection_messages": 0,
            "buffered_detection_messages": 0,
            "camera_info_messages": 0,
            "rgb_messages": 0,
            "depth_messages": 0,
            "imu_messages": 0,
            "pose_messages": 0,
            "detection_messages": 0,
            "source_modes_seen": [],
        }

        self.create_subscription(CameraInfo, args.camera_info_topic, self._on_camera_info, 10)
        self.create_subscription(Image, args.rgb_topic, self._on_rgb, 10)
        self.create_subscription(Image, args.depth_topic, self._on_depth, 10)
        self.create_subscription(Imu, args.imu_topic, self._on_imu, 10)
        self.create_subscription(Odometry, args.pose_topic, self._on_pose, 10)
        self.create_subscription(String, args.detections_topic, self._on_detections, 10)
        self.create_timer(0.5, self._check_idle_timeout)

        self.get_logger().info(
            f"semantic mapper running in {args.mode} mode with output {self.output_path}"
        )

    def _on_camera_info(self, msg: CameraInfo) -> None:
        self.metrics["camera_info_messages"] += 1
        self.latest_intrinsics = CameraIntrinsics(
            fx=float(msg.k[0]),
            fy=float(msg.k[4]),
            cx=float(msg.k[2]),
            cy=float(msg.k[5]),
        )
        self._drain_pending_detections()

    def _on_rgb(self, _: Image) -> None:
        self.metrics["rgb_messages"] += 1

    def _on_depth(self, _: Image) -> None:
        self.metrics["depth_messages"] += 1

    def _on_imu(self, _: Imu) -> None:
        self.metrics["imu_messages"] += 1

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
        self.latest_pose_frame_id = msg.header.frame_id
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
        if envelope.source_mode not in self.metrics["source_modes_seen"]:
            self.metrics["source_modes_seen"].append(envelope.source_mode)

        observation = build_frame_observation(
            frame_id=envelope.frame_id,
            pose=self.latest_pose,
            intrinsics=self.latest_intrinsics,
            detections=envelope.detections,
        )
        self.builder.add_frame(observation)
        self.metrics["frames_processed"] += 1
        self.last_frame_time = time.monotonic()

        if self.expected_frames and self.metrics["frames_processed"] >= self.expected_frames:
            self.finalize(reason="expected_frames_reached")

    def _check_idle_timeout(self) -> None:
        if self.finalized:
            return
        if self.metrics["frames_processed"] == 0 or self.last_frame_time is None:
            return
        if (time.monotonic() - self.last_frame_time) >= self.idle_timeout_s:
            self.finalize(reason="idle_timeout")

    def finalize(self, *, reason: str) -> None:
        if self.finalized:
            return
        self.finalized = True

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.builder.export_to_path(self.output_path)
        query_paths = export_query_results(self.builder, self.query_labels, self.query_output_dir)
        self.metrics["skipped_detection_messages"] += len(self.pending_detection_payloads)
        self.pending_detection_payloads.clear()

        runtime_summary = {
            **self.metrics,
            "finalize_reason": reason,
            "output_path": str(self.output_path),
            "query_outputs": [str(path) for path in query_paths],
            "pose_frame_id": self.latest_pose_frame_id,
        }
        runtime_path = self.output_path.with_name(f"{self.output_path.stem}_runtime.json")
        runtime_path.write_text(json.dumps(runtime_summary, indent=2), encoding="utf-8")
        self.get_logger().info(json.dumps(runtime_summary, indent=2))


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ROS topic driven Phase 1 semantic mapper.")
    parser.add_argument("--mode", choices=["fixture", "bag_replay", "live_isaac"], required=True)
    parser.add_argument("--fixture", help="Fixture JSON used by fixture mode or replay helpers.")
    parser.add_argument("--output", required=True, help="Semantic map output path.")
    parser.add_argument(
        "--query-output-dir",
        default="/home/peng/AgentSlam/artifacts/phase1",
        help="Directory for exported query JSON files.",
    )
    parser.add_argument("--query-label", action="append", default=[], help="Query label to export.")
    parser.add_argument("--merge-distance", type=float, default=0.75, help="Merge distance in meters.")
    parser.add_argument("--expected-frames", type=int, default=0, help="Finalize after this many frames if >0.")
    parser.add_argument("--idle-timeout", type=float, default=3.0, help="Finalize after this much idle time.")
    parser.add_argument("--camera-info-topic", default="/agentslam/camera/rgb/camera_info")
    parser.add_argument("--rgb-topic", default="/agentslam/camera/rgb/image_raw")
    parser.add_argument("--depth-topic", default="/agentslam/camera/depth/image_raw")
    parser.add_argument("--imu-topic", default="/agentslam/imu/data")
    parser.add_argument("--pose-topic", default="/agentslam/gt/odom")
    parser.add_argument("--detections-topic", default="/agentslam/semantic_detections")
    return parser.parse_args(argv)


def run_fixture_mode(args: argparse.Namespace) -> int:
    if not args.fixture:
        raise SystemExit("--fixture is required when --mode fixture")
    payload = build_map_from_fixture(
        fixture_path=args.fixture,
        output_path=args.output,
        merge_distance_m=args.merge_distance,
    )
    builder = SemanticMapBuilder(merge_distance_m=args.merge_distance)
    from .io import load_fixture

    for frame in load_fixture(args.fixture):
        builder.add_frame(frame)
    query_paths = export_query_results(builder, args.query_label, args.query_output_dir)
    runtime_path = Path(args.output).with_name(f"{Path(args.output).stem}_runtime.json")
    runtime_path.write_text(
        json.dumps(
            {
                "mode": "fixture",
                "frames_processed": len(load_fixture(args.fixture)),
                "output_path": str(Path(args.output)),
                "query_outputs": [str(path) for path in query_paths],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"map": payload, "query_outputs": [str(path) for path in query_paths]}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.mode == "fixture":
        return run_fixture_mode(args)

    rclpy.init(args=None)
    node = SemanticMapperNode(args)
    try:
        while rclpy.ok() and not node.finalized:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        if not node.finalized:
            node.finalize(reason="keyboard_interrupt")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
