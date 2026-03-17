#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node


@dataclass
class PoseSample:
    stamp_s: float
    x: float
    y: float
    yaw_rad: float


def wrap_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def odom_to_sample(msg: Odometry) -> PoseSample:
    stamp_s = float(msg.header.stamp.sec) + float(msg.header.stamp.nanosec) * 1e-9
    pose = msg.pose.pose
    orientation = pose.orientation
    return PoseSample(
        stamp_s=stamp_s,
        x=float(pose.position.x),
        y=float(pose.position.y),
        yaw_rad=quaternion_to_yaw(
            float(orientation.x),
            float(orientation.y),
            float(orientation.z),
            float(orientation.w),
        ),
    )


def relative_pose(a: PoseSample, b: PoseSample) -> PoseSample:
    dx_world = b.x - a.x
    dy_world = b.y - a.y
    cos_yaw = math.cos(a.yaw_rad)
    sin_yaw = math.sin(a.yaw_rad)
    dx_local = cos_yaw * dx_world + sin_yaw * dy_world
    dy_local = -sin_yaw * dx_world + cos_yaw * dy_world
    return PoseSample(
        stamp_s=b.stamp_s - a.stamp_s,
        x=dx_local,
        y=dy_local,
        yaw_rad=wrap_angle(b.yaw_rad - a.yaw_rad),
    )


def normalize_to_start(samples: list[PoseSample]) -> list[PoseSample]:
    if not samples:
        return []
    origin = samples[0]
    cos_yaw = math.cos(origin.yaw_rad)
    sin_yaw = math.sin(origin.yaw_rad)
    normalized: list[PoseSample] = []
    for sample in samples:
        dx_world = sample.x - origin.x
        dy_world = sample.y - origin.y
        dx_local = cos_yaw * dx_world + sin_yaw * dy_world
        dy_local = -sin_yaw * dx_world + cos_yaw * dy_world
        normalized.append(
            PoseSample(
                stamp_s=sample.stamp_s - origin.stamp_s,
                x=dx_local,
                y=dy_local,
                yaw_rad=wrap_angle(sample.yaw_rad - origin.yaw_rad),
            )
        )
    return normalized


def translation_error(a: PoseSample, b: PoseSample) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def pose_translation_distance(a: PoseSample, b: PoseSample) -> float:
    return math.hypot(b.x - a.x, b.y - a.y)


def match_by_nearest_time(
    reference_samples: list[PoseSample],
    estimate_samples: list[PoseSample],
    max_dt_s: float,
) -> list[tuple[PoseSample, PoseSample, float]]:
    if not reference_samples or not estimate_samples:
        return []

    matches: list[tuple[PoseSample, PoseSample, float]] = []
    est_idx = 0

    for ref in reference_samples:
        while est_idx + 1 < len(estimate_samples):
            current_dt = abs(estimate_samples[est_idx].stamp_s - ref.stamp_s)
            next_dt = abs(estimate_samples[est_idx + 1].stamp_s - ref.stamp_s)
            if next_dt <= current_dt:
                est_idx += 1
            else:
                break
        estimate = estimate_samples[est_idx]
        dt = estimate.stamp_s - ref.stamp_s
        if abs(dt) <= max_dt_s:
            matches.append((ref, estimate, dt))

    return matches


def rmse(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(v * v for v in values) / len(values))


def mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def max_value(values: list[float]) -> float:
    if not values:
        return 0.0
    return max(values)


def compute_path_length(samples: list[PoseSample]) -> float:
    if len(samples) < 2:
        return 0.0
    return sum(pose_translation_distance(samples[i], samples[i + 1]) for i in range(len(samples) - 1))


def compute_rpe(
    matches: list[tuple[PoseSample, PoseSample, float]],
    interval_s: float,
) -> tuple[list[float], list[float]]:
    if len(matches) < 2:
        return [], []

    ref_matches = [m[0] for m in matches]
    est_matches = [m[1] for m in matches]
    rpe_translation_errors: list[float] = []
    rpe_yaw_errors: list[float] = []
    j = 1

    for i in range(len(matches) - 1):
        target_time = ref_matches[i].stamp_s + interval_s
        while j < len(matches) and ref_matches[j].stamp_s < target_time:
            j += 1
        if j >= len(matches):
            break
        ref_delta = relative_pose(ref_matches[i], ref_matches[j])
        est_delta = relative_pose(est_matches[i], est_matches[j])
        rpe_translation_errors.append(translation_error(ref_delta, est_delta))
        rpe_yaw_errors.append(abs(wrap_angle(ref_delta.yaw_rad - est_delta.yaw_rad)))

    return rpe_translation_errors, rpe_yaw_errors


class OdomRecorder(Node):
    def __init__(self, reference_topic: str, estimate_topic: str) -> None:
        super().__init__("agentslam_vslam_accuracy_recorder")
        self.reference_samples: list[PoseSample] = []
        self.estimate_samples: list[PoseSample] = []
        self.create_subscription(Odometry, reference_topic, self._on_reference, 100)
        self.create_subscription(Odometry, estimate_topic, self._on_estimate, 100)

    def _on_reference(self, msg: Odometry) -> None:
        self.reference_samples.append(odom_to_sample(msg))

    def _on_estimate(self, msg: Odometry) -> None:
        self.estimate_samples.append(odom_to_sample(msg))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate an odometry topic against a reference odometry topic.")
    parser.add_argument("--reference-topic", default="/chassis/odom")
    parser.add_argument("--estimate-topic", default="/agentslam/localization/odom")
    parser.add_argument("--duration-seconds", type=float, default=20.0)
    parser.add_argument("--warmup-seconds", type=float, default=2.0)
    parser.add_argument("--max-match-dt-seconds", type=float, default=0.05)
    parser.add_argument("--rpe-interval-seconds", type=float, default=1.0)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-matches-json", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rclpy.init()
    node = OdomRecorder(args.reference_topic, args.estimate_topic)

    start_time = time.monotonic()
    end_time = start_time + max(args.duration_seconds, 0.1)
    warmup_end = start_time + max(args.warmup_seconds, 0.0)

    try:
        while time.monotonic() < end_time:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()

    reference_samples = [s for s in node.reference_samples if s.stamp_s >= 0.0]
    estimate_samples = [s for s in node.estimate_samples if s.stamp_s >= 0.0]

    matches = match_by_nearest_time(reference_samples, estimate_samples, args.max_match_dt_seconds)
    warm_matches = [m for m in matches if m[0].stamp_s >= (matches[0][0].stamp_s + args.warmup_seconds)] if matches else []
    usable_matches = warm_matches if warm_matches else matches

    raw_matched_reference = [m[0] for m in usable_matches]
    raw_matched_estimate = [m[1] for m in usable_matches]
    matched_reference = normalize_to_start(raw_matched_reference)
    matched_estimate = normalize_to_start(raw_matched_estimate)
    normalized_matches = [
        (matched_reference[index], matched_estimate[index], usable_matches[index][2]) for index in range(len(usable_matches))
    ]

    translation_errors = [translation_error(ref, est) for ref, est, _ in normalized_matches]
    yaw_errors = [abs(wrap_angle(ref.yaw_rad - est.yaw_rad)) for ref, est, _ in normalized_matches]
    match_dts = [abs(dt) for _, _, dt in normalized_matches]

    rpe_translation_errors, rpe_yaw_errors = compute_rpe(normalized_matches, args.rpe_interval_seconds)

    end_pose_translation_error = (
        translation_error(matched_reference[-1], matched_estimate[-1]) if usable_matches else 0.0
    )
    end_pose_yaw_error = (
        abs(wrap_angle(matched_reference[-1].yaw_rad - matched_estimate[-1].yaw_rad)) if usable_matches else 0.0
    )

    payload = {
        "reference_topic": args.reference_topic,
        "estimate_topic": args.estimate_topic,
        "duration_seconds": args.duration_seconds,
        "warmup_seconds": args.warmup_seconds,
        "max_match_dt_seconds": args.max_match_dt_seconds,
        "rpe_interval_seconds": args.rpe_interval_seconds,
        "reference_sample_count": len(reference_samples),
        "estimate_sample_count": len(estimate_samples),
        "matched_sample_count": len(usable_matches),
        "comparison_frame": "each trajectory normalized to its own first matched pose",
        "reference_path_length_m": compute_path_length(matched_reference),
        "estimate_path_length_m": compute_path_length(matched_estimate),
        "translation_rmse_m": rmse(translation_errors),
        "translation_mean_m": mean(translation_errors),
        "translation_max_m": max_value(translation_errors),
        "yaw_rmse_deg": math.degrees(rmse(yaw_errors)),
        "yaw_mean_deg": math.degrees(mean(yaw_errors)),
        "yaw_max_deg": math.degrees(max_value(yaw_errors)),
        "match_dt_mean_ms": mean(match_dts) * 1000.0,
        "match_dt_max_ms": max_value(match_dts) * 1000.0,
        "rpe_translation_rmse_m": rmse(rpe_translation_errors),
        "rpe_translation_mean_m": mean(rpe_translation_errors),
        "rpe_yaw_rmse_deg": math.degrees(rmse(rpe_yaw_errors)),
        "rpe_yaw_mean_deg": math.degrees(mean(rpe_yaw_errors)),
        "end_pose_translation_error_m": end_pose_translation_error,
        "end_pose_yaw_error_deg": math.degrees(end_pose_yaw_error),
    }

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2) + "\n")

    if args.output_matches_json:
        matches_payload = [
            {
                "reference_raw": asdict(raw_matched_reference[index]),
                "estimate_raw": asdict(raw_matched_estimate[index]),
                "reference_normalized": asdict(ref),
                "estimate_normalized": asdict(est),
                "time_delta_ms": normalized_matches[index][2] * 1000.0,
                "translation_error_m": translation_error(ref, est),
                "yaw_error_deg": math.degrees(abs(wrap_angle(ref.yaw_rad - est.yaw_rad))),
            }
            for index, (ref, est, _dt) in enumerate(normalized_matches)
        ]
        output_matches = Path(args.output_matches_json)
        output_matches.parent.mkdir(parents=True, exist_ok=True)
        output_matches.write_text(json.dumps(matches_payload, indent=2) + "\n")

    if len(usable_matches) < 5:
        raise SystemExit(
            f"insufficient matched samples for evaluation: {len(usable_matches)} matches from "
            f"{len(reference_samples)} reference and {len(estimate_samples)} estimate samples"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
