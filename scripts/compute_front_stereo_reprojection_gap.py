#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np


EXPECTED_STATIC_TF = {
    "left": {
        "translation": np.array([0.100299996844566, 0.074998001555137, 0.345899982084279], dtype=np.float64),
        "quaternion_xyzw": np.array(
            [-0.499999999344188, 0.500000009409837, -0.499999980788213, 0.500000010457762],
            dtype=np.float64,
        ),
    },
    "right": {
        "translation": np.array([0.100299992374257, -0.075001996994339, 0.345900005926137], dtype=np.float64),
        "quaternion_xyzw": np.array(
            [-0.499999999344188, 0.500000009409837, -0.499999980788213, 0.500000010457762],
            dtype=np.float64,
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute pixel reprojection gap caused by using the current static TF instead of actual Nova stereo extrinsics."
    )
    parser.add_argument("--camera-contract-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--report-md", required=True)
    parser.add_argument("--left-overlay", required=True)
    parser.add_argument("--right-overlay", required=True)
    parser.add_argument("--board-distance-m", type=float, default=2.0)
    parser.add_argument("--board-inner-cols", type=int, default=6)
    parser.add_argument("--board-inner-rows", type=int, default=10)
    parser.add_argument("--board-square-size-m", type=float, default=0.035)
    return parser.parse_args()


def normalize(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm <= 1e-9:
        raise ValueError("cannot normalize near-zero vector")
    return vec / norm


def quaternion_xyzw_to_matrix(quat_xyzw: np.ndarray) -> np.ndarray:
    x, y, z, w = quat_xyzw
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return np.array(
        [
            [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
            [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
            [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
        ],
        dtype=np.float64,
    )


def rotation_matrix_to_quaternion_xyzw(rotation: np.ndarray) -> np.ndarray:
    trace = float(np.trace(rotation))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (rotation[2, 1] - rotation[1, 2]) / s
        y = (rotation[0, 2] - rotation[2, 0]) / s
        z = (rotation[1, 0] - rotation[0, 1]) / s
    elif rotation[0, 0] > rotation[1, 1] and rotation[0, 0] > rotation[2, 2]:
        s = math.sqrt(1.0 + rotation[0, 0] - rotation[1, 1] - rotation[2, 2]) * 2.0
        w = (rotation[2, 1] - rotation[1, 2]) / s
        x = 0.25 * s
        y = (rotation[0, 1] + rotation[1, 0]) / s
        z = (rotation[0, 2] + rotation[2, 0]) / s
    elif rotation[1, 1] > rotation[2, 2]:
        s = math.sqrt(1.0 + rotation[1, 1] - rotation[0, 0] - rotation[2, 2]) * 2.0
        w = (rotation[0, 2] - rotation[2, 0]) / s
        x = (rotation[0, 1] + rotation[1, 0]) / s
        y = 0.25 * s
        z = (rotation[1, 2] + rotation[2, 1]) / s
    else:
        s = math.sqrt(1.0 + rotation[2, 2] - rotation[0, 0] - rotation[1, 1]) * 2.0
        w = (rotation[1, 0] - rotation[0, 1]) / s
        x = (rotation[0, 2] + rotation[2, 0]) / s
        y = (rotation[1, 2] + rotation[2, 1]) / s
        z = 0.25 * s
    quat = np.array([x, y, z, w], dtype=np.float64)
    return quat / np.linalg.norm(quat)


def quaternion_angle_error_deg(actual_xyzw: np.ndarray, expected_xyzw: np.ndarray) -> float:
    actual = actual_xyzw / np.linalg.norm(actual_xyzw)
    expected = expected_xyzw / np.linalg.norm(expected_xyzw)
    dot = abs(float(np.clip(np.dot(actual, expected), -1.0, 1.0)))
    return math.degrees(2.0 * math.acos(dot))


def make_transform(translation: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation
    return transform


def invert_transform(transform: np.ndarray) -> np.ndarray:
    rotation = transform[:3, :3]
    translation = transform[:3, 3]
    inverse = np.eye(4, dtype=np.float64)
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -rotation.T @ translation
    return inverse


def transform_points(transform: np.ndarray, points: np.ndarray) -> np.ndarray:
    hom = np.concatenate([points, np.ones((points.shape[0], 1), dtype=np.float64)], axis=1)
    return (transform @ hom.T).T[:, :3]


def project_points(k_matrix: np.ndarray, world_t_camera_ros: np.ndarray, world_points: np.ndarray) -> np.ndarray:
    camera_t_world = invert_transform(world_t_camera_ros)
    camera_points = transform_points(camera_t_world, world_points)
    z = camera_points[:, 2:3]
    if np.any(z <= 1e-4):
        raise RuntimeError("board points are behind camera or too close to optical center")
    uvw = (k_matrix @ camera_points.T).T
    return uvw[:, :2] / z


def build_checkerboard_world_points(
    *,
    left_world_t_camera_ros: np.ndarray,
    right_world_t_camera_ros: np.ndarray,
    board_distance_m: float,
    inner_cols: int,
    inner_rows: int,
    square_size_m: float,
) -> tuple[np.ndarray, dict[str, list[float]]]:
    left_position = left_world_t_camera_ros[:3, 3]
    right_position = right_world_t_camera_ros[:3, 3]
    midpoint = (left_position + right_position) * 0.5
    forward = normalize((left_world_t_camera_ros[:3, 2] + right_world_t_camera_ros[:3, 2]) * 0.5)
    board_normal = forward
    up_reference = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    if abs(float(np.dot(up_reference, board_normal))) > 0.95:
        up_reference = np.array([0.0, 1.0, 0.0], dtype=np.float64)
    board_x = normalize(np.cross(up_reference, board_normal))
    board_y = normalize(np.cross(board_normal, board_x))
    board_rotation = np.column_stack([board_x, board_y, board_normal])
    board_center_world = midpoint + forward * board_distance_m

    col_offsets = (np.arange(inner_cols, dtype=np.float64) - (inner_cols - 1) * 0.5) * square_size_m
    row_offsets = (np.arange(inner_rows, dtype=np.float64) - (inner_rows - 1) * 0.5) * square_size_m
    points = []
    for row in row_offsets:
        for col in col_offsets:
            local = np.array([col, row, 0.0], dtype=np.float64)
            points.append(board_center_world + board_rotation @ local)
    return np.asarray(points, dtype=np.float64), {
        "center_world_m": board_center_world.tolist(),
        "quaternion_xyzw": rotation_matrix_to_quaternion_xyzw(board_rotation).tolist(),
        "square_size_m": float(square_size_m),
        "inner_cols": int(inner_cols),
        "inner_rows": int(inner_rows),
    }


def draw_projection_delta(
    width: int,
    height: int,
    actual_pixels: np.ndarray,
    expected_pixels: np.ndarray | None,
    output_path: Path,
) -> None:
    canvas = np.full((height, width, 3), 245, dtype=np.uint8)
    if expected_pixels is None:
        for actual_point in actual_pixels:
            actual_xy = tuple(np.round(actual_point).astype(int))
            cv2.circle(canvas, actual_xy, 4, (38, 166, 91), -1)
        cv2.putText(
            canvas,
            "expected static TF points are behind camera",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (207, 52, 52),
            2,
            cv2.LINE_AA,
        )
    else:
        for actual_point, expected_point in zip(actual_pixels, expected_pixels):
            actual_xy = tuple(np.round(actual_point).astype(int))
            expected_xy = tuple(np.round(expected_point).astype(int))
            cv2.line(canvas, actual_xy, expected_xy, (255, 210, 50), 1)
            cv2.circle(canvas, actual_xy, 4, (38, 166, 91), -1)
            cv2.circle(canvas, expected_xy, 4, (207, 52, 52), -1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), canvas)


def main() -> int:
    args = parse_args()
    contract = json.loads(Path(args.camera_contract_json).read_text(encoding="utf-8"))
    output_json = Path(args.output_json)
    report_md = Path(args.report_md)
    left_overlay = Path(args.left_overlay)
    right_overlay = Path(args.right_overlay)
    for path in (output_json, report_md, left_overlay, right_overlay):
        path.parent.mkdir(parents=True, exist_ok=True)

    width = int(contract["resolution"]["width"])
    height = int(contract["resolution"]["height"])
    world_t_chassis = np.asarray(contract["world_t_chassis"], dtype=np.float64)
    left_intrinsics = np.asarray(contract["left_camera"]["intrinsics_matrix"], dtype=np.float64)
    right_intrinsics = np.asarray(contract["right_camera"]["intrinsics_matrix"], dtype=np.float64)
    left_world_t_camera_ros = np.asarray(contract["left_camera"]["world_t_camera_ros"], dtype=np.float64)
    right_world_t_camera_ros = np.asarray(contract["right_camera"]["world_t_camera_ros"], dtype=np.float64)

    chassis_t_left_actual = invert_transform(world_t_chassis) @ left_world_t_camera_ros
    chassis_t_right_actual = invert_transform(world_t_chassis) @ right_world_t_camera_ros
    chassis_t_left_expected = make_transform(
        EXPECTED_STATIC_TF["left"]["translation"],
        quaternion_xyzw_to_matrix(EXPECTED_STATIC_TF["left"]["quaternion_xyzw"]),
    )
    chassis_t_right_expected = make_transform(
        EXPECTED_STATIC_TF["right"]["translation"],
        quaternion_xyzw_to_matrix(EXPECTED_STATIC_TF["right"]["quaternion_xyzw"]),
    )
    world_t_left_expected = world_t_chassis @ chassis_t_left_expected
    world_t_right_expected = world_t_chassis @ chassis_t_right_expected

    board_world_points, board_pose_summary = build_checkerboard_world_points(
        left_world_t_camera_ros=left_world_t_camera_ros,
        right_world_t_camera_ros=right_world_t_camera_ros,
        board_distance_m=float(args.board_distance_m),
        inner_cols=int(args.board_inner_cols),
        inner_rows=int(args.board_inner_rows),
        square_size_m=float(args.board_square_size_m),
    )

    left_pixels_actual = project_points(left_intrinsics, left_world_t_camera_ros, board_world_points)
    right_pixels_actual = project_points(right_intrinsics, right_world_t_camera_ros, board_world_points)
    left_expected_projection_error: str | None = None
    right_expected_projection_error: str | None = None
    try:
        left_pixels_expected = project_points(left_intrinsics, world_t_left_expected, board_world_points)
        left_pixel_error = np.linalg.norm(left_pixels_actual - left_pixels_expected, axis=1)
    except RuntimeError as exc:
        left_pixels_expected = None
        left_pixel_error = None
        left_expected_projection_error = str(exc)
    try:
        right_pixels_expected = project_points(right_intrinsics, world_t_right_expected, board_world_points)
        right_pixel_error = np.linalg.norm(right_pixels_actual - right_pixels_expected, axis=1)
    except RuntimeError as exc:
        right_pixels_expected = None
        right_pixel_error = None
        right_expected_projection_error = str(exc)
    draw_projection_delta(width, height, left_pixels_actual, left_pixels_expected, left_overlay)
    draw_projection_delta(width, height, right_pixels_actual, right_pixels_expected, right_overlay)

    left_actual_quat = rotation_matrix_to_quaternion_xyzw(chassis_t_left_actual[:3, :3])
    right_actual_quat = rotation_matrix_to_quaternion_xyzw(chassis_t_right_actual[:3, :3])
    left_translation_error = chassis_t_left_actual[:3, 3] - EXPECTED_STATIC_TF["left"]["translation"]
    right_translation_error = chassis_t_right_actual[:3, 3] - EXPECTED_STATIC_TF["right"]["translation"]

    left_projection_visible = left_pixel_error is not None
    right_projection_visible = right_pixel_error is not None
    payload = {
        "camera_contract_json": args.camera_contract_json,
        "resolution": {"width": width, "height": height},
        "synthetic_board_pose": board_pose_summary,
        "left_camera": {
            "fx": float(left_intrinsics[0, 0]),
            "fy": float(left_intrinsics[1, 1]),
            "cx": float(left_intrinsics[0, 2]),
            "cy": float(left_intrinsics[1, 2]),
            "actual_chassis_to_camera_ros_translation_m": chassis_t_left_actual[:3, 3].tolist(),
            "actual_chassis_to_camera_ros_quaternion_xyzw": left_actual_quat.tolist(),
            "expected_static_tf_translation_m": EXPECTED_STATIC_TF["left"]["translation"].tolist(),
            "expected_static_tf_quaternion_xyzw": EXPECTED_STATIC_TF["left"]["quaternion_xyzw"].tolist(),
            "translation_error_m": left_translation_error.tolist(),
            "translation_error_norm_m": float(np.linalg.norm(left_translation_error)),
            "rotation_error_deg": float(
                quaternion_angle_error_deg(left_actual_quat, EXPECTED_STATIC_TF["left"]["quaternion_xyzw"])
            ),
            "expected_projection_visible": bool(left_projection_visible),
            "expected_projection_error": left_expected_projection_error,
            "reprojection_gap_rmse_px": (
                float(np.sqrt(np.mean(np.square(left_pixel_error)))) if left_pixel_error is not None else None
            ),
            "reprojection_gap_max_px": float(np.max(left_pixel_error)) if left_pixel_error is not None else None,
            "reprojection_gap_mean_px": float(np.mean(left_pixel_error)) if left_pixel_error is not None else None,
            "overlay_path": str(left_overlay),
        },
        "right_camera": {
            "fx": float(right_intrinsics[0, 0]),
            "fy": float(right_intrinsics[1, 1]),
            "cx": float(right_intrinsics[0, 2]),
            "cy": float(right_intrinsics[1, 2]),
            "actual_chassis_to_camera_ros_translation_m": chassis_t_right_actual[:3, 3].tolist(),
            "actual_chassis_to_camera_ros_quaternion_xyzw": right_actual_quat.tolist(),
            "expected_static_tf_translation_m": EXPECTED_STATIC_TF["right"]["translation"].tolist(),
            "expected_static_tf_quaternion_xyzw": EXPECTED_STATIC_TF["right"]["quaternion_xyzw"].tolist(),
            "translation_error_m": right_translation_error.tolist(),
            "translation_error_norm_m": float(np.linalg.norm(right_translation_error)),
            "rotation_error_deg": float(
                quaternion_angle_error_deg(right_actual_quat, EXPECTED_STATIC_TF["right"]["quaternion_xyzw"])
            ),
            "expected_projection_visible": bool(right_projection_visible),
            "expected_projection_error": right_expected_projection_error,
            "reprojection_gap_rmse_px": (
                float(np.sqrt(np.mean(np.square(right_pixel_error)))) if right_pixel_error is not None else None
            ),
            "reprojection_gap_max_px": float(np.max(right_pixel_error)) if right_pixel_error is not None else None,
            "reprojection_gap_mean_px": float(np.mean(right_pixel_error)) if right_pixel_error is not None else None,
            "overlay_path": str(right_overlay),
        },
    }
    valid_rmse = [
        value
        for value in (
            payload["left_camera"]["reprojection_gap_rmse_px"],
            payload["right_camera"]["reprojection_gap_rmse_px"],
        )
        if value is not None
    ]
    payload["stereo_reprojection_gap_rmse_px_mean"] = float(np.mean(valid_rmse)) if valid_rmse else None

    output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_md.write_text(
        "\n".join(
            [
                "# PHASE1_FRONT_STEREO_GEOMETRY_AUDIT",
                "",
                "## Summary",
                "- This is a geometry-only audit.",
                "- We first dump the actual Nova stereo camera contract from Isaac Sim, then estimate how many pixels the same board would move if we used the current published static TF instead of the actual camera pose.",
                "",
                "## Left Camera",
                f"- fx/fy/cx/cy: `{payload['left_camera']['fx']:.3f}` / `{payload['left_camera']['fy']:.3f}` / `{payload['left_camera']['cx']:.3f}` / `{payload['left_camera']['cy']:.3f}`",
                f"- translation error norm: `{payload['left_camera']['translation_error_norm_m']:.6f}` m",
                f"- rotation error: `{payload['left_camera']['rotation_error_deg']:.6f}` deg",
                f"- expected projection visible: `{payload['left_camera']['expected_projection_visible']}`",
                f"- reprojection gap RMSE: `{payload['left_camera']['reprojection_gap_rmse_px']}`",
                f"- reprojection gap max: `{payload['left_camera']['reprojection_gap_max_px']}`",
                f"- expected projection error: `{payload['left_camera']['expected_projection_error']}`",
                f"- overlay: `{left_overlay}`",
                "",
                "## Right Camera",
                f"- fx/fy/cx/cy: `{payload['right_camera']['fx']:.3f}` / `{payload['right_camera']['fy']:.3f}` / `{payload['right_camera']['cx']:.3f}` / `{payload['right_camera']['cy']:.3f}`",
                f"- translation error norm: `{payload['right_camera']['translation_error_norm_m']:.6f}` m",
                f"- rotation error: `{payload['right_camera']['rotation_error_deg']:.6f}` deg",
                f"- expected projection visible: `{payload['right_camera']['expected_projection_visible']}`",
                f"- reprojection gap RMSE: `{payload['right_camera']['reprojection_gap_rmse_px']}`",
                f"- reprojection gap max: `{payload['right_camera']['reprojection_gap_max_px']}`",
                f"- expected projection error: `{payload['right_camera']['expected_projection_error']}`",
                f"- overlay: `{right_overlay}`",
                "",
                "## Synthetic Board",
                f"- pose summary: `{board_pose_summary}`",
                "",
                "## JSON",
                f"- metrics: `{output_json}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
