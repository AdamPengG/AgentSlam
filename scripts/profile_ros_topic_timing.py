#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rosidl_runtime_py.utilities import get_message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture receive timing, header timing, and simple motion stats for a set of ROS topics."
    )
    parser.add_argument(
        "--topic",
        action="append",
        required=True,
        help="Topic specification in the form /name:pkg/msg/Type[:label]",
    )
    parser.add_argument("--duration-seconds", type=float, default=45.0)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-samples-json", default="")
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=400,
        help="Maximum callback samples retained per topic in the optional samples JSON.",
    )
    return parser.parse_args()


@dataclass
class TopicSpec:
    name: str
    type_name: str
    label: str


@dataclass
class TopicState:
    name: str
    type_name: str
    label: str
    count: int = 0
    first_receive_offset_s: float | None = None
    last_receive_offset_s: float | None = None
    receive_offsets_s: list[float] = field(default_factory=list)
    receive_gap_ms: list[float] = field(default_factory=list)
    header_offsets_s: list[float] = field(default_factory=list)
    header_gap_ms: list[float] = field(default_factory=list)
    second_bins: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    sample_rows: list[dict[str, Any]] = field(default_factory=list)
    last_receive_ns: int | None = None
    last_header_ns: int | None = None
    last_position_xy: tuple[float, float] | None = None
    pose_path_length_m: float = 0.0
    pose_step_jumps_m: list[float] = field(default_factory=list)
    first_pose_xy: tuple[float, float] | None = None
    last_pose_xy: tuple[float, float] | None = None
    latest_linear_speed_mps: float | None = None
    latest_angular_speed_radps: float | None = None


def parse_topic_spec(raw_value: str) -> TopicSpec:
    pieces = raw_value.split(":")
    if len(pieces) not in (2, 3):
        raise ValueError(f"invalid topic spec '{raw_value}', expected /name:pkg/msg/Type[:label]")
    name, type_name = pieces[0].strip(), pieces[1].strip()
    label = pieces[2].strip() if len(pieces) == 3 else name.strip("/")
    if not name.startswith("/"):
        raise ValueError(f"topic name must be absolute: {raw_value}")
    return TopicSpec(name=name, type_name=type_name, label=label)


def _header_stamp_ns(msg: Any) -> int | None:
    header = getattr(msg, "header", None)
    if header is None:
        return None
    stamp = getattr(header, "stamp", None)
    if stamp is None:
        return None
    return int(stamp.sec) * 1_000_000_000 + int(stamp.nanosec)


def _pose_xy(msg: Any) -> tuple[float, float] | None:
    if isinstance(msg, Odometry):
        position = msg.pose.pose.position
        return float(position.x), float(position.y)
    return None


def _velocity_summary(msg: Any) -> tuple[float | None, float | None]:
    if isinstance(msg, Odometry):
        twist = msg.twist.twist
        return float(twist.linear.x), float(twist.angular.z)
    if isinstance(msg, Twist):
        return float(msg.linear.x), float(msg.angular.z)
    return None, None


def _mean(values: list[float]) -> float:
    return float(statistics.fmean(values)) if values else 0.0


def _rmse(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(v * v for v in values) / len(values))


class TimingProfilerNode(Node):
    def __init__(self, specs: list[TopicSpec], duration_seconds: float, sample_limit: int) -> None:
        super().__init__("agentslam_topic_timing_profiler")
        self._sample_limit = max(1, sample_limit)
        self._duration_seconds = float(duration_seconds)
        self._start_mono_ns = time.monotonic_ns()
        self._states: dict[str, TopicState] = {
            spec.name: TopicState(name=spec.name, type_name=spec.type_name, label=spec.label) for spec in specs
        }
        self._done = False

        for spec in specs:
            message_type = get_message(spec.type_name)
            self.create_subscription(
                message_type,
                spec.name,
                lambda msg, topic_name=spec.name: self._callback(topic_name, msg),
                qos_profile_sensor_data,
            )

        self.create_timer(0.25, self._tick)

    @property
    def done(self) -> bool:
        return self._done

    @property
    def duration_seconds(self) -> float:
        return self._duration_seconds

    def states(self) -> dict[str, TopicState]:
        return self._states

    def _tick(self) -> None:
        elapsed_s = (time.monotonic_ns() - self._start_mono_ns) / 1_000_000_000.0
        if elapsed_s >= self._duration_seconds:
            self._done = True

    def _callback(self, topic_name: str, msg: Any) -> None:
        now_mono_ns = time.monotonic_ns()
        state = self._states[topic_name]
        receive_offset_s = (now_mono_ns - self._start_mono_ns) / 1_000_000_000.0
        header_ns = _header_stamp_ns(msg)

        state.count += 1
        if state.first_receive_offset_s is None:
            state.first_receive_offset_s = receive_offset_s
        state.last_receive_offset_s = receive_offset_s
        state.receive_offsets_s.append(receive_offset_s)
        state.second_bins[int(receive_offset_s)] += 1

        if state.last_receive_ns is not None:
            state.receive_gap_ms.append((now_mono_ns - state.last_receive_ns) / 1_000_000.0)
        state.last_receive_ns = now_mono_ns

        header_offset_s = None
        if header_ns is not None:
            header_offset_s = header_ns / 1_000_000_000.0
            state.header_offsets_s.append(header_offset_s)
            if state.last_header_ns is not None:
                state.header_gap_ms.append((header_ns - state.last_header_ns) / 1_000_000.0)
            state.last_header_ns = header_ns

        pose_xy = _pose_xy(msg)
        if pose_xy is not None:
            if state.first_pose_xy is None:
                state.first_pose_xy = pose_xy
            if state.last_position_xy is not None:
                dx = pose_xy[0] - state.last_position_xy[0]
                dy = pose_xy[1] - state.last_position_xy[1]
                step_jump_m = math.hypot(dx, dy)
                state.pose_path_length_m += step_jump_m
                state.pose_step_jumps_m.append(step_jump_m)
            state.last_position_xy = pose_xy
            state.last_pose_xy = pose_xy

        linear_speed_mps, angular_speed_radps = _velocity_summary(msg)
        if linear_speed_mps is not None:
            state.latest_linear_speed_mps = linear_speed_mps
        if angular_speed_radps is not None:
            state.latest_angular_speed_radps = angular_speed_radps

        if len(state.sample_rows) < self._sample_limit:
            sample_row: dict[str, Any] = {
                "receive_offset_s": round(receive_offset_s, 6),
                "count_index": state.count,
            }
            if header_offset_s is not None:
                sample_row["header_offset_s"] = round(header_offset_s, 6)
            if pose_xy is not None:
                sample_row["pose_xy"] = [round(pose_xy[0], 6), round(pose_xy[1], 6)]
            if linear_speed_mps is not None:
                sample_row["linear_speed_mps"] = round(linear_speed_mps, 6)
            if angular_speed_radps is not None:
                sample_row["angular_speed_radps"] = round(angular_speed_radps, 6)
            state.sample_rows.append(sample_row)


def build_summary(node: TimingProfilerNode) -> dict[str, Any]:
    duration_seconds = node.duration_seconds
    topics_summary: dict[str, Any] = {}

    for topic_name, state in node.states().items():
        tail_silence_s = (
            max(0.0, duration_seconds - state.last_receive_offset_s)
            if state.last_receive_offset_s is not None
            else duration_seconds
        )
        window_tail_10s = 0
        if state.receive_offsets_s:
            window_tail_10s = sum(1 for value in state.receive_offsets_s if value >= max(0.0, duration_seconds - 10.0))

        pose_displacement_m = None
        if state.first_pose_xy is not None and state.last_pose_xy is not None:
            pose_displacement_m = math.hypot(
                state.last_pose_xy[0] - state.first_pose_xy[0],
                state.last_pose_xy[1] - state.first_pose_xy[1],
            )

        topics_summary[topic_name] = {
            "label": state.label,
            "type_name": state.type_name,
            "count": state.count,
            "first_receive_offset_s": state.first_receive_offset_s,
            "last_receive_offset_s": state.last_receive_offset_s,
            "tail_silence_s": tail_silence_s,
            "mean_receive_hz": (state.count / duration_seconds) if duration_seconds > 0.0 else 0.0,
            "messages_last_10s": window_tail_10s,
            "receive_gap_mean_ms": _mean(state.receive_gap_ms),
            "receive_gap_max_ms": max(state.receive_gap_ms) if state.receive_gap_ms else 0.0,
            "receive_gap_rmse_ms": _rmse(state.receive_gap_ms),
            "header_gap_mean_ms": _mean(state.header_gap_ms),
            "header_gap_max_ms": max(state.header_gap_ms) if state.header_gap_ms else 0.0,
            "header_gap_rmse_ms": _rmse(state.header_gap_ms),
            "pose_path_length_m": state.pose_path_length_m,
            "pose_displacement_m": pose_displacement_m,
            "pose_step_jump_mean_m": _mean(state.pose_step_jumps_m),
            "pose_step_jump_max_m": max(state.pose_step_jumps_m) if state.pose_step_jumps_m else 0.0,
            "pose_step_jump_count_gt_1m": sum(1 for value in state.pose_step_jumps_m if value > 1.0),
            "latest_linear_speed_mps": state.latest_linear_speed_mps,
            "latest_angular_speed_radps": state.latest_angular_speed_radps,
            "second_bins": {str(key): value for key, value in sorted(state.second_bins.items())},
        }

    return {
        "capture_duration_seconds": duration_seconds,
        "wall_start_unix_s": time.time(),
        "topics": topics_summary,
    }


def main() -> int:
    args = parse_args()
    specs = [parse_topic_spec(value) for value in args.topic]
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    samples_path = Path(args.output_samples_json) if args.output_samples_json else None
    if samples_path is not None:
        samples_path.parent.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = TimingProfilerNode(specs=specs, duration_seconds=args.duration_seconds, sample_limit=args.sample_limit)
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
        summary = build_summary(node)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        if samples_path is not None:
            samples_payload = {
                topic_name: state.sample_rows
                for topic_name, state in node.states().items()
            }
            samples_path.write_text(json.dumps(samples_payload, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
