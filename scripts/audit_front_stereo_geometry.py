#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import cv2
import numpy as np
from isaacsim import SimulationApp


EXPECTED_STATIC_TF = {
    "left": {
        "translation": np.array([0.1003, 0.074998, 0.3459], dtype=np.float64),
        "quaternion_xyzw": np.array(
            [-0.5000000000000001, 0.5000000000000001, 0.5000000000000001, -0.49999999999999983],
            dtype=np.float64,
        ),
    },
    "right": {
        "translation": np.array([0.1003, -0.075002, 0.3459], dtype=np.float64),
        "quaternion_xyzw": np.array(
            [-0.5000000000000001, 0.5000000000000001, 0.5000000000000001, -0.49999999999999983],
            dtype=np.float64,
        ),
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Nova front stereo intrinsics/extrinsics and estimate reprojection gap caused by static TF error."
    )
    parser.add_argument(
        "--scene",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd",
    )
    parser.add_argument(
        "--robot",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd",
    )
    parser.add_argument("--robot-prim-path", default="/World/NovaCarter")
    parser.add_argument("--chassis-prim", default="/World/NovaCarter/chassis_link")
    parser.add_argument("--left-camera-prim", default="/World/NovaCarter/chassis_link/sensors/front_hawk/left/camera_left")
    parser.add_argument(
        "--right-camera-prim", default="/World/NovaCarter/chassis_link/sensors/front_hawk/right/camera_right"
    )
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--report-md", required=True)
    parser.add_argument("--left-overlay", required=True)
    parser.add_argument("--right-overlay", required=True)
    parser.add_argument("--resolution-width", type=int, default=1280)
    parser.add_argument("--resolution-height", type=int, default=720)
    parser.add_argument("--board-distance-m", type=float, default=2.0)
    parser.add_argument("--board-inner-cols", type=int, default=6)
    parser.add_argument("--board-inner-rows", type=int, default=10)
    parser.add_argument("--board-square-size-m", type=float, default=0.035)
    parser.add_argument("--warmup-frames", type=int, default=45)
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


def quaternion_wxyz_to_matrix(quat_wxyz: np.ndarray) -> np.ndarray:
    w, x, y, z = quat_wxyz
    return quaternion_xyzw_to_matrix(np.array([x, y, z, w], dtype=np.float64))


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
    board_normal = -forward
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
    expected_pixels: np.ndarray,
    output_path: Path,
) -> None:
    canvas = np.full((height, width, 3), 245, dtype=np.uint8)
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
    output_json = Path(args.output_json)
    report_md = Path(args.report_md)
    left_overlay = Path(args.left_overlay)
    right_overlay = Path(args.right_overlay)
    for path in (output_json, report_md, left_overlay, right_overlay):
        path.parent.mkdir(parents=True, exist_ok=True)

    app = SimulationApp(
        {
            "headless": True,
            "disable_viewport_updates": True,
            "multi_gpu": False,
            "max_gpu_count": 1,
            "active_gpu": 0,
            "physics_gpu": 0,
            "width": int(args.resolution_width),
            "height": int(args.resolution_height),
        }
    )
    try:
        print("geometry_audit: app_started", flush=True)
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading, open_stage
        from isaacsim.core.utils.xforms import get_world_pose
        from isaacsim.sensors.camera import Camera

        open_stage(args.scene)
        app.update()
        app.update()
        while is_stage_loading():
            app.update()
        print("geometry_audit: scene_loaded", flush=True)

        add_reference_to_stage(args.robot, args.robot_prim_path)
        for _ in range(max(1, int(args.warmup_frames))):
            app.update()
        print("geometry_audit: robot_added", flush=True)

        sim = SimulationContext(stage_units_in_meters=1.0)
        sim.play()
        for _ in range(5):
            sim.step(render=False)
        print("geometry_audit: sim_started", flush=True)

        resolution = (int(args.resolution_width), int(args.resolution_height))
        left_camera = Camera(prim_path=args.left_camera_prim, name="left_geometry_audit", resolution=resolution)
        right_camera = Camera(prim_path=args.right_camera_prim, name="right_geometry_audit", resolution=resolution)
        left_camera.initialize()
        right_camera.initialize()
        print("geometry_audit: cameras_initialized", flush=True)

        left_intrinsics = np.asarray(left_camera.get_intrinsics_matrix(), dtype=np.float64)
        right_intrinsics = np.asarray(right_camera.get_intrinsics_matrix(), dtype=np.float64)
        left_world_t_camera_ros = invert_transform(np.asarray(left_camera.get_view_matrix_ros(), dtype=np.float64))
        right_world_t_camera_ros = invert_transform(np.asarray(right_camera.get_view_matrix_ros(), dtype=np.float64))
        print("geometry_audit: camera_pose_loaded", flush=True)

        chassis_position, chassis_quaternion_wxyz = get_world_pose(args.chassis_prim)
        world_t_chassis = make_transform(
            np.asarray(chassis_position, dtype=np.float64),
            quaternion_wxyz_to_matrix(np.asarray(chassis_quaternion_wxyz, dtype=np.float64)),
        )

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
        print("geometry_audit: board_points_ready", flush=True)

        left_pixels_actual = project_points(left_intrinsics, left_world_t_camera_ros, board_world_points)
        right_pixels_actual = project_points(right_intrinsics, right_world_t_camera_ros, board_world_points)
        left_pixels_expected = project_points(left_intrinsics, world_t_left_expected, board_world_points)
        right_pixels_expected = project_points(right_intrinsics, world_t_right_expected, board_world_points)
        print("geometry_audit: projections_ready", flush=True)

        left_pixel_error = np.linalg.norm(left_pixels_actual - left_pixels_expected, axis=1)
        right_pixel_error = np.linalg.norm(right_pixels_actual - right_pixels_expected, axis=1)
        draw_projection_delta(
            int(args.resolution_width),
            int(args.resolution_height),
            left_pixels_actual,
            left_pixels_expected,
            left_overlay,
        )
        print("geometry_audit: overlays_written", flush=True)
        draw_projection_delta(
            int(args.resolution_width),
            int(args.resolution_height),
            right_pixels_actual,
            right_pixels_expected,
            right_overlay,
        )

        left_actual_quat = rotation_matrix_to_quaternion_xyzw(chassis_t_left_actual[:3, :3])
        right_actual_quat = rotation_matrix_to_quaternion_xyzw(chassis_t_right_actual[:3, :3])
        left_translation_error = chassis_t_left_actual[:3, 3] - EXPECTED_STATIC_TF["left"]["translation"]
        right_translation_error = chassis_t_right_actual[:3, 3] - EXPECTED_STATIC_TF["right"]["translation"]

        payload = {
            "scene": args.scene,
            "robot": args.robot,
            "resolution": {"width": int(args.resolution_width), "height": int(args.resolution_height)},
            "synthetic_board_pose": board_pose_summary,
            "left_camera": {
                "prim_path": args.left_camera_prim,
                "intrinsics_matrix": left_intrinsics.tolist(),
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
                "reprojection_gap_rmse_px": float(np.sqrt(np.mean(np.square(left_pixel_error)))),
                "reprojection_gap_max_px": float(np.max(left_pixel_error)),
                "reprojection_gap_mean_px": float(np.mean(left_pixel_error)),
                "overlay_path": str(left_overlay),
            },
            "right_camera": {
                "prim_path": args.right_camera_prim,
                "intrinsics_matrix": right_intrinsics.tolist(),
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
                "reprojection_gap_rmse_px": float(np.sqrt(np.mean(np.square(right_pixel_error)))),
                "reprojection_gap_max_px": float(np.max(right_pixel_error)),
                "reprojection_gap_mean_px": float(np.mean(right_pixel_error)),
                "overlay_path": str(right_overlay),
            },
        }
        payload["stereo_reprojection_gap_rmse_px_mean"] = float(
            (payload["left_camera"]["reprojection_gap_rmse_px"] + payload["right_camera"]["reprojection_gap_rmse_px"])
            * 0.5
        )

        output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        report_md.write_text(
            "\n".join(
                [
                    "# PHASE1_FRONT_STEREO_GEOMETRY_AUDIT",
                    "",
                    "## Summary",
                    "- This is a geometry-based audit using the real Nova camera intrinsics and actual stage extrinsics.",
                    "- Reprojection gap here means: for the same synthetic checkerboard in world coordinates, how many pixels the image projection would shift if we used the current published static TF instead of the actual camera pose from Isaac Sim.",
                    "",
                    "## Left Camera",
                    f"- fx/fy/cx/cy: `{payload['left_camera']['fx']:.3f}` / `{payload['left_camera']['fy']:.3f}` / `{payload['left_camera']['cx']:.3f}` / `{payload['left_camera']['cy']:.3f}`",
                    f"- translation error norm: `{payload['left_camera']['translation_error_norm_m']:.6f}` m",
                    f"- rotation error: `{payload['left_camera']['rotation_error_deg']:.6f}` deg",
                    f"- reprojection gap RMSE: `{payload['left_camera']['reprojection_gap_rmse_px']:.3f}` px",
                    f"- reprojection gap max: `{payload['left_camera']['reprojection_gap_max_px']:.3f}` px",
                    f"- overlay: `{left_overlay}`",
                    "",
                    "## Right Camera",
                    f"- fx/fy/cx/cy: `{payload['right_camera']['fx']:.3f}` / `{payload['right_camera']['fy']:.3f}` / `{payload['right_camera']['cx']:.3f}` / `{payload['right_camera']['cy']:.3f}`",
                    f"- translation error norm: `{payload['right_camera']['translation_error_norm_m']:.6f}` m",
                    f"- rotation error: `{payload['right_camera']['rotation_error_deg']:.6f}` deg",
                    f"- reprojection gap RMSE: `{payload['right_camera']['reprojection_gap_rmse_px']:.3f}` px",
                    f"- reprojection gap max: `{payload['right_camera']['reprojection_gap_max_px']:.3f}` px",
                    f"- overlay: `{right_overlay}`",
                    "",
                    "## Synthetic Board",
                    f"- board pose summary: `{board_pose_summary}`",
                    "",
                    "## JSON",
                    f"- metrics: `{output_json}`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        print("geometry_audit: reports_written", flush=True)
        sim.stop()
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
