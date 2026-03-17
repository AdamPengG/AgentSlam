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
        description="Render a Nova front-stereo checkerboard scene and audit intrinsics/extrinsics via reprojection."
    )
    parser.add_argument(
        "--scene",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd",
    )
    parser.add_argument(
        "--robot",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd",
    )
    parser.add_argument(
        "--checkerboard-usd",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Props/Camera/checkerboard_6x10.usd",
    )
    parser.add_argument("--robot-prim-path", default="/World/NovaCarter")
    parser.add_argument("--checkerboard-prim-path", default="/World/CalibrationTarget")
    parser.add_argument("--left-camera-prim", default="/World/NovaCarter/chassis_link/sensors/front_hawk/left/camera_left")
    parser.add_argument(
        "--right-camera-prim", default="/World/NovaCarter/chassis_link/sensors/front_hawk/right/camera_right"
    )
    parser.add_argument("--chassis-prim", default="/World/NovaCarter/chassis_link")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--report-md", required=True)
    parser.add_argument("--left-raw", required=True)
    parser.add_argument("--right-raw", required=True)
    parser.add_argument("--left-overlay", required=True)
    parser.add_argument("--right-overlay", required=True)
    parser.add_argument("--resolution-width", type=int, default=1280)
    parser.add_argument("--resolution-height", type=int, default=720)
    parser.add_argument("--checkerboard-inner-cols", type=int, default=6)
    parser.add_argument("--checkerboard-inner-rows", type=int, default=10)
    parser.add_argument("--board-distance-m", type=float, default=2.0)
    parser.add_argument("--warmup-frames", type=int, default=90)
    parser.add_argument("--settle-frames", type=int, default=60)
    parser.add_argument("--capture-frames", type=int, default=15)
    parser.add_argument("--headless", action="store_true", default=True)
    return parser.parse_args()


def normalize(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm <= 1e-9:
        raise ValueError("cannot normalize near-zero vector")
    return vec / norm


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


def wrap_angle_rad(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def quaternion_angle_error_deg(actual_xyzw: np.ndarray, expected_xyzw: np.ndarray) -> float:
    actual = actual_xyzw / np.linalg.norm(actual_xyzw)
    expected = expected_xyzw / np.linalg.norm(expected_xyzw)
    dot = abs(float(np.clip(np.dot(actual, expected), -1.0, 1.0)))
    return math.degrees(2.0 * math.acos(dot))


def ensure_bgr(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image)
    if image.ndim != 3:
        raise ValueError(f"expected HxWxC image, got shape {image.shape}")
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    raise ValueError(f"unexpected channel count: {image.shape[2]}")


def detect_chessboard(gray: np.ndarray, pattern_size: tuple[int, int]) -> np.ndarray:
    if hasattr(cv2, "findChessboardCornersSB"):
        found, corners = cv2.findChessboardCornersSB(gray, pattern_size, cv2.CALIB_CB_EXHAUSTIVE)
        if found:
            return corners.reshape((-1, 2)).astype(np.float64)
    flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
    found, corners = cv2.findChessboardCorners(gray, pattern_size, flags)
    if not found:
        raise RuntimeError(f"could not find checkerboard corners for pattern {pattern_size}")
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 1e-3)
    refined = cv2.cornerSubPix(gray, corners, (9, 9), (-1, -1), criteria)
    return refined.reshape((-1, 2)).astype(np.float64)


def draw_overlay(image_bgr: np.ndarray, detected: np.ndarray, projected: np.ndarray) -> np.ndarray:
    overlay = image_bgr.copy()
    for point in projected:
        cv2.circle(overlay, tuple(np.round(point).astype(int)), 5, (0, 0, 255), 2)
    for point in detected:
        cv2.circle(overlay, tuple(np.round(point).astype(int)), 4, (0, 255, 0), -1)
    for detected_point, projected_point in zip(detected, projected):
        cv2.line(
            overlay,
            tuple(np.round(detected_point).astype(int)),
            tuple(np.round(projected_point).astype(int)),
            (255, 255, 0),
            1,
        )
    return overlay


def build_candidate_local_corner_grids(
    local_min: np.ndarray,
    local_max: np.ndarray,
    inner_cols: int,
    inner_rows: int,
) -> list[np.ndarray]:
    size = local_max - local_min
    plane_axes = list(np.argsort(size)[-2:])
    normal_axis = [axis for axis in range(3) if axis not in plane_axes][0]
    local_mid = (local_min + local_max) * 0.5
    candidates: list[np.ndarray] = []
    for swap in (False, True):
        cols_axis, rows_axis = (plane_axes[0], plane_axes[1]) if not swap else (plane_axes[1], plane_axes[0])
        col_step = size[cols_axis] / float(inner_cols + 1)
        row_step = size[rows_axis] / float(inner_rows + 1)
        base_cols = np.linspace(local_min[cols_axis] + col_step, local_max[cols_axis] - col_step, inner_cols)
        base_rows = np.linspace(local_min[rows_axis] + row_step, local_max[rows_axis] - row_step, inner_rows)
        for reverse_cols in (False, True):
            cols = base_cols[::-1] if reverse_cols else base_cols
            for reverse_rows in (False, True):
                rows = base_rows[::-1] if reverse_rows else base_rows
                points = []
                for row_value in rows:
                    for col_value in cols:
                        point = local_mid.copy()
                        point[normal_axis] = local_mid[normal_axis]
                        point[cols_axis] = col_value
                        point[rows_axis] = row_value
                        points.append(point)
                candidates.append(np.asarray(points, dtype=np.float64))
    return candidates


def compute_candidate_error(projected: np.ndarray, detected: np.ndarray) -> tuple[float, float]:
    residual = projected - detected
    norms = np.linalg.norm(residual, axis=1)
    rmse = float(np.sqrt(np.mean(np.square(norms))))
    return rmse, float(np.max(norms))


def main() -> int:
    args = parse_args()
    output_json = Path(args.output_json)
    report_md = Path(args.report_md)
    left_raw = Path(args.left_raw)
    right_raw = Path(args.right_raw)
    left_overlay = Path(args.left_overlay)
    right_overlay = Path(args.right_overlay)
    for path in (output_json, report_md, left_raw, right_raw, left_overlay, right_overlay):
        path.parent.mkdir(parents=True, exist_ok=True)

    app = SimulationApp({"headless": args.headless, "disable_viewport_updates": args.headless})
    try:
        import omni
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading, open_stage
        from isaacsim.core.utils.xforms import get_world_pose
        from isaacsim.sensors.camera import Camera
        from pxr import Gf, UsdGeom

        open_stage(str(Path(args.scene).resolve()))
        app.update()
        app.update()
        while is_stage_loading():
            app.update()

        add_reference_to_stage(str(Path(args.robot).resolve()), str(args.robot_prim_path))
        add_reference_to_stage(str(Path(args.checkerboard_usd).resolve()), str(args.checkerboard_prim_path))
        for _ in range(max(1, int(args.warmup_frames))):
            app.update()

        sim = SimulationContext(stage_units_in_meters=1.0)
        sim.play()
        for _ in range(10):
            sim.step(render=True)

        resolution = (int(args.resolution_width), int(args.resolution_height))
        left_camera = Camera(prim_path=str(args.left_camera_prim), name="phase1_left_calibration", resolution=resolution)
        right_camera = Camera(prim_path=str(args.right_camera_prim), name="phase1_right_calibration", resolution=resolution)
        left_camera.initialize()
        right_camera.initialize()

        for _ in range(10):
            sim.step(render=True)

        left_world_t_camera_ros = invert_transform(np.asarray(left_camera.get_view_matrix_ros(), dtype=np.float64))
        right_world_t_camera_ros = invert_transform(np.asarray(right_camera.get_view_matrix_ros(), dtype=np.float64))
        left_position = left_world_t_camera_ros[:3, 3]
        right_position = right_world_t_camera_ros[:3, 3]
        forward = normalize((left_world_t_camera_ros[:3, 2] + right_world_t_camera_ros[:3, 2]) * 0.5)
        midpoint = (left_position + right_position) * 0.5
        normal = -forward
        up_reference = np.array([0.0, 0.0, 1.0], dtype=np.float64)
        if abs(float(np.dot(up_reference, normal))) > 0.95:
            up_reference = np.array([0.0, 1.0, 0.0], dtype=np.float64)
        board_x = normalize(np.cross(up_reference, normal))
        board_y = normalize(np.cross(normal, board_x))
        board_rotation = np.column_stack([board_x, board_y, normal])
        board_quaternion_xyzw = rotation_matrix_to_quaternion_xyzw(board_rotation)
        board_center_world = midpoint + forward * float(args.board_distance_m)

        stage = omni.usd.get_context().get_stage()
        checkerboard_prim = stage.GetPrimAtPath(str(args.checkerboard_prim_path))
        checkerboard_xform = UsdGeom.Xformable(checkerboard_prim)
        checkerboard_xform.ClearXformOpOrder()
        checkerboard_xform.AddTranslateOp().Set(Gf.Vec3d(*board_center_world.tolist()))
        checkerboard_xform.AddOrientOp().Set(
            Gf.Quatd(float(board_quaternion_xyzw[3]), Gf.Vec3d(*board_quaternion_xyzw[:3].tolist()))
        )

        for _ in range(max(1, int(args.settle_frames))):
            sim.step(render=True)

        left_image = None
        right_image = None
        for _ in range(max(1, int(args.capture_frames))):
            sim.step(render=True)
            left_image = left_camera.get_rgb()
            right_image = right_camera.get_rgb()
        if left_image is None or right_image is None:
            raise RuntimeError("camera render products did not produce RGB frames")

        left_bgr = ensure_bgr(np.asarray(left_image))
        right_bgr = ensure_bgr(np.asarray(right_image))
        cv2.imwrite(str(left_raw), left_bgr)
        cv2.imwrite(str(right_raw), right_bgr)

        pattern_size = (int(args.checkerboard_inner_cols), int(args.checkerboard_inner_rows))
        left_corners = detect_chessboard(cv2.cvtColor(left_bgr, cv2.COLOR_BGR2GRAY), pattern_size)
        right_corners = detect_chessboard(cv2.cvtColor(right_bgr, cv2.COLOR_BGR2GRAY), pattern_size)

        bbox_cache = UsdGeom.BBoxCache(0.0, [UsdGeom.Tokens.default_], useExtentsHint=True)
        local_range = bbox_cache.ComputeLocalBound(checkerboard_prim).ComputeAlignedRange()
        local_min = np.asarray(local_range.GetMin(), dtype=np.float64)
        local_max = np.asarray(local_range.GetMax(), dtype=np.float64)
        world_t_checkerboard = np.transpose(
            np.asarray(UsdGeom.Imageable(checkerboard_prim).ComputeLocalToWorldTransform(0.0), dtype=np.float64)
        )
        candidate_local_points = build_candidate_local_corner_grids(
            local_min=local_min,
            local_max=local_max,
            inner_cols=int(args.checkerboard_inner_cols),
            inner_rows=int(args.checkerboard_inner_rows),
        )

        best = None
        for local_points in candidate_local_points:
            world_points = transform_points(world_t_checkerboard, local_points)
            projected_left = np.asarray(left_camera.get_image_coords_from_world_points(world_points), dtype=np.float64)
            projected_right = np.asarray(right_camera.get_image_coords_from_world_points(world_points), dtype=np.float64)
            left_rmse, left_max = compute_candidate_error(projected_left, left_corners)
            right_rmse, right_max = compute_candidate_error(projected_right, right_corners)
            mean_rmse = (left_rmse + right_rmse) * 0.5
            if best is None or mean_rmse < best["mean_rmse"]:
                best = {
                    "mean_rmse": mean_rmse,
                    "world_points": world_points,
                    "local_points": local_points,
                    "projected_left": projected_left,
                    "projected_right": projected_right,
                    "left_rmse": left_rmse,
                    "left_max": left_max,
                    "right_rmse": right_rmse,
                    "right_max": right_max,
                }
        if best is None:
            raise RuntimeError("failed to build reprojection candidate set")

        left_overlay_bgr = draw_overlay(left_bgr, left_corners, best["projected_left"])
        right_overlay_bgr = draw_overlay(right_bgr, right_corners, best["projected_right"])
        cv2.imwrite(str(left_overlay), left_overlay_bgr)
        cv2.imwrite(str(right_overlay), right_overlay_bgr)

        chassis_position, chassis_quaternion_wxyz = get_world_pose(str(args.chassis_prim))
        world_t_chassis = make_transform(
            np.asarray(chassis_position, dtype=np.float64),
            quaternion_wxyz_to_matrix(np.asarray(chassis_quaternion_wxyz, dtype=np.float64)),
        )
        chassis_t_left_ros = invert_transform(world_t_chassis) @ left_world_t_camera_ros
        chassis_t_right_ros = invert_transform(world_t_chassis) @ right_world_t_camera_ros

        actual_left_translation = chassis_t_left_ros[:3, 3]
        actual_right_translation = chassis_t_right_ros[:3, 3]
        actual_left_quaternion_xyzw = rotation_matrix_to_quaternion_xyzw(chassis_t_left_ros[:3, :3])
        actual_right_quaternion_xyzw = rotation_matrix_to_quaternion_xyzw(chassis_t_right_ros[:3, :3])

        left_translation_error = actual_left_translation - EXPECTED_STATIC_TF["left"]["translation"]
        right_translation_error = actual_right_translation - EXPECTED_STATIC_TF["right"]["translation"]

        left_intrinsics = np.asarray(left_camera.get_intrinsics_matrix(), dtype=np.float64)
        right_intrinsics = np.asarray(right_camera.get_intrinsics_matrix(), dtype=np.float64)

        payload = {
            "scene": str(args.scene),
            "robot": str(args.robot),
            "checkerboard": str(args.checkerboard_usd),
            "checkerboard_inner_pattern": {
                "cols": int(args.checkerboard_inner_cols),
                "rows": int(args.checkerboard_inner_rows),
            },
            "resolution": {
                "width": int(resolution[0]),
                "height": int(resolution[1]),
            },
            "board_pose_world": {
                "translation": board_center_world.tolist(),
                "quaternion_xyzw": board_quaternion_xyzw.tolist(),
            },
            "board_local_bbox_size_m": (local_max - local_min).tolist(),
            "camera_models": {
                "left_lens_model": str(left_camera.get_lens_distortion_model()),
                "right_lens_model": str(right_camera.get_lens_distortion_model()),
            },
            "left_camera": {
                "prim_path": str(args.left_camera_prim),
                "intrinsics_matrix": left_intrinsics.tolist(),
                "fx": float(left_intrinsics[0, 0]),
                "fy": float(left_intrinsics[1, 1]),
                "cx": float(left_intrinsics[0, 2]),
                "cy": float(left_intrinsics[1, 2]),
                "actual_chassis_to_camera_ros_translation_m": actual_left_translation.tolist(),
                "actual_chassis_to_camera_ros_quaternion_xyzw": actual_left_quaternion_xyzw.tolist(),
                "expected_static_tf_translation_m": EXPECTED_STATIC_TF["left"]["translation"].tolist(),
                "expected_static_tf_quaternion_xyzw": EXPECTED_STATIC_TF["left"]["quaternion_xyzw"].tolist(),
                "translation_error_m": left_translation_error.tolist(),
                "translation_error_norm_m": float(np.linalg.norm(left_translation_error)),
                "rotation_error_deg": float(
                    quaternion_angle_error_deg(
                        actual_left_quaternion_xyzw,
                        EXPECTED_STATIC_TF["left"]["quaternion_xyzw"],
                    )
                ),
                "detected_corner_count": int(left_corners.shape[0]),
                "reprojection_rmse_px": float(best["left_rmse"]),
                "reprojection_max_error_px": float(best["left_max"]),
                "raw_image_path": str(left_raw),
                "overlay_path": str(left_overlay),
            },
            "right_camera": {
                "prim_path": str(args.right_camera_prim),
                "intrinsics_matrix": right_intrinsics.tolist(),
                "fx": float(right_intrinsics[0, 0]),
                "fy": float(right_intrinsics[1, 1]),
                "cx": float(right_intrinsics[0, 2]),
                "cy": float(right_intrinsics[1, 2]),
                "actual_chassis_to_camera_ros_translation_m": actual_right_translation.tolist(),
                "actual_chassis_to_camera_ros_quaternion_xyzw": actual_right_quaternion_xyzw.tolist(),
                "expected_static_tf_translation_m": EXPECTED_STATIC_TF["right"]["translation"].tolist(),
                "expected_static_tf_quaternion_xyzw": EXPECTED_STATIC_TF["right"]["quaternion_xyzw"].tolist(),
                "translation_error_m": right_translation_error.tolist(),
                "translation_error_norm_m": float(np.linalg.norm(right_translation_error)),
                "rotation_error_deg": float(
                    quaternion_angle_error_deg(
                        actual_right_quaternion_xyzw,
                        EXPECTED_STATIC_TF["right"]["quaternion_xyzw"],
                    )
                ),
                "detected_corner_count": int(right_corners.shape[0]),
                "reprojection_rmse_px": float(best["right_rmse"]),
                "reprojection_max_error_px": float(best["right_max"]),
                "raw_image_path": str(right_raw),
                "overlay_path": str(right_overlay),
            },
            "stereo_reprojection_mean_rmse_px": float(best["mean_rmse"]),
        }
        output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        report_md.write_text(
            "\n".join(
                [
                    "# PHASE1_FRONT_STEREO_CALIBRATION_AUDIT",
                    "",
                    "## Summary",
                    f"- stereo reprojection mean RMSE: `{payload['stereo_reprojection_mean_rmse_px']:.3f}` px",
                    f"- left translation error norm: `{payload['left_camera']['translation_error_norm_m']:.5f}` m",
                    f"- right translation error norm: `{payload['right_camera']['translation_error_norm_m']:.5f}` m",
                    f"- left rotation error: `{payload['left_camera']['rotation_error_deg']:.3f}` deg",
                    f"- right rotation error: `{payload['right_camera']['rotation_error_deg']:.3f}` deg",
                    "",
                    "## Left Camera",
                    f"- intrinsics: fx=`{payload['left_camera']['fx']:.3f}` fy=`{payload['left_camera']['fy']:.3f}` cx=`{payload['left_camera']['cx']:.3f}` cy=`{payload['left_camera']['cy']:.3f}`",
                    f"- raw image: `{left_raw}`",
                    f"- overlay: `{left_overlay}`",
                    "",
                    "## Right Camera",
                    f"- intrinsics: fx=`{payload['right_camera']['fx']:.3f}` fy=`{payload['right_camera']['fy']:.3f}` cx=`{payload['right_camera']['cx']:.3f}` cy=`{payload['right_camera']['cy']:.3f}`",
                    f"- raw image: `{right_raw}`",
                    f"- overlay: `{right_overlay}`",
                    "",
                    "## Checkerboard",
                    f"- checkerboard asset: `{args.checkerboard_usd}`",
                    f"- board pose world: `{payload['board_pose_world']}`",
                    f"- bbox size: `{payload['board_local_bbox_size_m']}`",
                    "",
                    "## JSON",
                    f"- metrics: `{output_json}`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        sim.stop()
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
