#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CameraInfo, Image
from tf2_msgs.msg import TFMessage


PATTERN_CANDIDATES = [(5, 9), (9, 5), (6, 10), (10, 6)]


@dataclass
class CameraCapture:
    image: np.ndarray | None = None
    camera_info: CameraInfo | None = None


def quaternion_to_rotation_matrix(x: float, y: float, z: float, w: float) -> np.ndarray:
    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z
    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=np.float64,
    )


def transform_to_matrix(translation: list[float], quaternion_xyzw: list[float]) -> np.ndarray:
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = quaternion_to_rotation_matrix(*quaternion_xyzw)
    matrix[:3, 3] = np.asarray(translation, dtype=np.float64)
    return matrix


def image_msg_to_numpy(msg: Image) -> np.ndarray:
    channels_by_encoding = {"mono8": 1, "rgb8": 3, "bgr8": 3, "rgba8": 4, "bgra8": 4}
    if msg.encoding not in channels_by_encoding:
        raise RuntimeError(f"unsupported image encoding: {msg.encoding}")
    channels = channels_by_encoding[msg.encoding]
    array = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width, channels))
    if msg.encoding == "rgb8":
        return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
    if msg.encoding == "rgba8":
        return cv2.cvtColor(array, cv2.COLOR_RGBA2BGR)
    if msg.encoding == "bgra8":
        return cv2.cvtColor(array, cv2.COLOR_BGRA2BGR)
    if msg.encoding == "mono8":
        return cv2.cvtColor(array[:, :, 0], cv2.COLOR_GRAY2BGR)
    return array


def project_points(camera_info: CameraInfo, points_camera: np.ndarray) -> np.ndarray:
    k = np.array(camera_info.k, dtype=np.float64).reshape((3, 3))
    x = points_camera[:, 0] / points_camera[:, 2]
    y = points_camera[:, 1] / points_camera[:, 2]
    uv = np.stack([k[0, 0] * x + k[0, 2], k[1, 1] * y + k[1, 2]], axis=1)
    return uv


def detect_checkerboard(image_bgr: np.ndarray) -> tuple[tuple[int, int], np.ndarray] | None:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    for pattern in PATTERN_CANDIDATES:
        found, corners = cv2.findChessboardCornersSB(gray, pattern, flags=cv2.CALIB_CB_EXHAUSTIVE)
        if found:
            return pattern, corners.reshape((-1, 2)).astype(np.float64)
    return None


def board_corner_grid(board_meta: dict, pattern: tuple[int, int]) -> np.ndarray:
    inner_cols, inner_rows = pattern
    width = float(board_meta["board_bbox_world_size_m"]["z"])
    height = float(board_meta["board_bbox_world_size_m"]["y"])
    if inner_cols <= 1 or inner_rows <= 1:
        raise RuntimeError(f"invalid checkerboard pattern: {pattern}")
    square_w = width / float(inner_cols + 1)
    square_h = height / float(inner_rows + 1)
    xs = np.linspace(-width / 2.0 + square_w, width / 2.0 - square_w, inner_cols)
    ys = np.linspace(height / 2.0 - square_h, -height / 2.0 + square_h, inner_rows)
    points = np.array([[0.0, y, x] for y in ys for x in xs], dtype=np.float64)
    return points


def reorder_variants(grid_points: np.ndarray, pattern: tuple[int, int]) -> list[np.ndarray]:
    cols, rows = pattern
    reshaped = grid_points.reshape((rows, cols, 3))
    return [
        reshaped.reshape((-1, 3)),
        reshaped[:, ::-1, :].reshape((-1, 3)),
        reshaped[::-1, :, :].reshape((-1, 3)),
        reshaped[::-1, ::-1, :].reshape((-1, 3)),
    ]


class StereoAuditNode(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("agentslam_front_stereo_reprojection_audit")
        self.left = CameraCapture()
        self.right = CameraCapture()
        self.transforms: dict[tuple[str, str], TransformStamped] = {}
        self.create_subscription(Image, args.left_image_topic, self._on_left_image, 10)
        self.create_subscription(CameraInfo, args.left_camera_info_topic, self._on_left_camera_info, 10)
        self.create_subscription(Image, args.right_image_topic, self._on_right_image, 10)
        self.create_subscription(CameraInfo, args.right_camera_info_topic, self._on_right_camera_info, 10)
        self.create_subscription(
            TFMessage,
            "/tf_static",
            self._on_tf_static,
            QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE),
        )

    def _on_left_image(self, msg: Image) -> None:
        if self.left.image is None:
            self.left.image = image_msg_to_numpy(msg)

    def _on_left_camera_info(self, msg: CameraInfo) -> None:
        if self.left.camera_info is None:
            self.left.camera_info = msg

    def _on_right_image(self, msg: Image) -> None:
        if self.right.image is None:
            self.right.image = image_msg_to_numpy(msg)

    def _on_right_camera_info(self, msg: CameraInfo) -> None:
        if self.right.camera_info is None:
            self.right.camera_info = msg

    def _on_tf_static(self, msg: TFMessage) -> None:
        for transform in msg.transforms:
            self.transforms[(transform.header.frame_id, transform.child_frame_id)] = transform

    def ready(self) -> bool:
        return (
            self.left.image is not None
            and self.left.camera_info is not None
            and self.right.image is not None
            and self.right.camera_info is not None
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the front stereo camera contract via checkerboard reprojection.")
    parser.add_argument("--board-meta-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--left-overlay", required=True)
    parser.add_argument("--right-overlay", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--left-image-topic", default="/front_stereo_camera/left/image_raw")
    parser.add_argument("--left-camera-info-topic", default="/front_stereo_camera/left/camera_info")
    parser.add_argument("--right-image-topic", default="/front_stereo_camera/right/image_raw")
    parser.add_argument("--right-camera-info-topic", default="/front_stereo_camera/right/camera_info")
    parser.add_argument("--left-optical-frame", default="front_stereo_camera_left_optical")
    parser.add_argument("--right-optical-frame", default="front_stereo_camera_right_optical")
    parser.add_argument("--chassis-frame", default="chassis_link")
    return parser.parse_args()


def camera_report(
    *,
    image_bgr: np.ndarray,
    camera_info: CameraInfo,
    board_points_chassis: np.ndarray,
    camera_from_chassis: np.ndarray,
    board_meta: dict,
    overlay_path: Path,
    label: str,
) -> dict:
    detection = detect_checkerboard(image_bgr)
    if detection is None:
        raise RuntimeError(f"{label}: checkerboard was not detected in the image")
    pattern, detected = detection
    model_points = board_corner_grid(board_meta, pattern)
    best = None

    board_from_chassis = transform_to_matrix(
        board_meta["board_pose_chassis"]["translation"],
        board_meta["board_pose_chassis"]["quaternion_xyzw"],
    )
    chassis_from_board = np.linalg.inv(board_from_chassis)

    for variant in reorder_variants(model_points, pattern):
        hom = np.concatenate([variant, np.ones((variant.shape[0], 1), dtype=np.float64)], axis=1)
        points_chassis = (board_from_chassis @ hom.T).T[:, :3]
        points_camera = (camera_from_chassis @ np.concatenate([points_chassis, np.ones((points_chassis.shape[0], 1))], axis=1).T).T[:, :3]
        valid = points_camera[:, 2] > 1e-6
        if not np.all(valid):
            continue
        projected = project_points(camera_info, points_camera)
        errors = np.linalg.norm(projected - detected, axis=1)
        rmse = float(np.sqrt(np.mean(errors * errors)))
        score = (rmse, float(np.max(errors)), projected, errors)
        if best is None or score[:2] < best[:2]:
            best = score

    if best is None:
        raise RuntimeError(f"{label}: all projection variants produced invalid camera-space points")

    rmse_px, max_error_px, projected, errors = best
    overlay = image_bgr.copy()
    for uv in detected:
        cv2.circle(overlay, tuple(np.round(uv).astype(int)), 5, (0, 255, 0), -1)
    for uv in projected:
        cv2.circle(overlay, tuple(np.round(uv).astype(int)), 3, (0, 0, 255), -1)
    cv2.putText(
        overlay,
        f"{label} reprojection RMSE {rmse_px:.2f}px max {max_error_px:.2f}px",
        (16, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 255, 0),
        2,
        cv2.LINE_AA,
    )
    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(overlay_path), overlay)

    return {
        "pattern": {"cols": int(pattern[0]), "rows": int(pattern[1])},
        "corner_count": int(len(detected)),
        "rmse_px": rmse_px,
        "max_error_px": max_error_px,
        "mean_error_px": float(np.mean(errors)),
        "camera_info_frame_id": camera_info.header.frame_id,
        "image_width": int(camera_info.width),
        "image_height": int(camera_info.height),
        "fx": float(camera_info.k[0]),
        "fy": float(camera_info.k[4]),
        "cx": float(camera_info.k[2]),
        "cy": float(camera_info.k[5]),
        "overlay_path": str(overlay_path),
    }


def main() -> int:
    args = parse_args()
    board_meta = json.loads(Path(args.board_meta_json).read_text(encoding="utf-8"))

    rclpy.init(args=[])
    node = StereoAuditNode(args)
    deadline = time.monotonic() + max(args.timeout_seconds, 1.0)
    try:
        while rclpy.ok() and time.monotonic() < deadline and not node.ready():
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            rclpy.shutdown()

    if not node.ready():
        raise RuntimeError("timed out waiting for stereo images and camera_info")

    left_from_chassis = transform_to_matrix(
        [0.1003, 0.074998, 0.3459],
        [-0.5000000000000001, 0.5000000000000001, 0.5000000000000001, -0.49999999999999983],
    )
    right_from_chassis = transform_to_matrix(
        [0.1003, -0.075002, 0.3459],
        [-0.5000000000000001, 0.5000000000000001, 0.5000000000000001, -0.49999999999999983],
    )

    left_report = camera_report(
        image_bgr=node.left.image,
        camera_info=node.left.camera_info,
        board_points_chassis=np.empty((0, 3), dtype=np.float64),
        camera_from_chassis=left_from_chassis,
        board_meta=board_meta,
        overlay_path=Path(args.left_overlay),
        label="left",
    )
    right_report = camera_report(
        image_bgr=node.right.image,
        camera_info=node.right.camera_info,
        board_points_chassis=np.empty((0, 3), dtype=np.float64),
        camera_from_chassis=right_from_chassis,
        board_meta=board_meta,
        overlay_path=Path(args.right_overlay),
        label="right",
    )

    result = {
        "board_meta_json": str(Path(args.board_meta_json).resolve()),
        "board_bbox_world_size_m": board_meta["board_bbox_world_size_m"],
        "board_pose_chassis": board_meta["board_pose_chassis"],
        "left_camera": left_report,
        "right_camera": right_report,
        "stereo_rmse_px_mean": float((left_report["rmse_px"] + right_report["rmse_px"]) / 2.0),
        "stereo_max_error_px": float(max(left_report["max_error_px"], right_report["max_error_px"])),
    }

    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
