#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
from pathlib import Path

import numpy as np
from isaacsim import SimulationApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Office + Nova with native ROS2 front stereo plus a fixed checkerboard target."
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
        "--checkerboard",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Props/Camera/checkerboard_6x10.usd",
    )
    parser.add_argument("--robot-prim-path", default="/World/NovaCarter")
    parser.add_argument("--checkerboard-prim-path", default="/World/Checkerboard")
    parser.add_argument("--camera-namespace", default="front_stereo_camera")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--warmup-frames", type=int, default=60)
    parser.add_argument("--publish-without-verification", action="store_true", default=True)
    parser.add_argument("--board-x-m", type=float, default=2.0)
    parser.add_argument("--board-y-m", type=float, default=0.0)
    parser.add_argument("--board-z-m", type=float, default=0.65)
    parser.add_argument("--board-roll-deg", type=float, default=90.0)
    parser.add_argument("--board-pitch-deg", type=float, default=90.0)
    parser.add_argument("--board-yaw-deg", type=float, default=0.0)
    parser.add_argument("--board-square-cols", type=int, default=6)
    parser.add_argument("--board-square-rows", type=int, default=10)
    parser.add_argument("--board-meta-json", required=True)
    return parser.parse_args()


def _set_enabled(controller: object, path: str, enabled: bool) -> None:
    attribute = controller.attribute(f"{path}.inputs:enabled")
    if attribute.is_valid():
        controller.set(attribute, enabled)


def _euler_xyz_to_quaternion(roll_rad: float, pitch_rad: float, yaw_rad: float) -> np.ndarray:
    cr = np.cos(roll_rad / 2.0)
    sr = np.sin(roll_rad / 2.0)
    cp = np.cos(pitch_rad / 2.0)
    sp = np.sin(pitch_rad / 2.0)
    cy = np.cos(yaw_rad / 2.0)
    sy = np.sin(yaw_rad / 2.0)
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    w = cr * cp * cy + sr * sp * sy
    return np.array([x, y, z, w], dtype=np.float64)


def main() -> int:
    args = parse_args()
    stop_requested = False

    def _request_stop(*_args: object) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    app = SimulationApp({"headless": args.headless, "disable_viewport_updates": args.headless})

    try:
        import carb
        import omni.graph.core as og
        import omni.usd
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.extensions import enable_extension
        from isaacsim.core.utils.prims import create_prim
        from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading, open_stage
        from isaacsim.core.utils.xforms import get_world_pose
        from pxr import Gf, UsdGeom

        scene_path = str(Path(args.scene).resolve())
        robot_path = str(Path(args.robot).resolve())
        checkerboard_path = str(Path(args.checkerboard).resolve())
        robot_prim_path = str(args.robot_prim_path)
        checkerboard_prim_path = str(args.checkerboard_prim_path)

        enable_extension("isaacsim.ros2.bridge")
        app.update()
        app.update()

        open_stage(scene_path)
        app.update()
        app.update()
        while is_stage_loading():
            app.update()

        add_reference_to_stage(robot_path, robot_prim_path)
        add_reference_to_stage(checkerboard_path, checkerboard_prim_path)
        for _ in range(max(1, int(args.warmup_frames))):
            app.update()

        if args.publish_without_verification:
            carb.settings.get_settings().set_bool("/exts/isaacsim.ros2.bridge/publish_without_verification", True)

        ros_graph = f"{robot_prim_path}/front_hawk"
        og.Controller.set(og.Controller.attribute(f"{ros_graph}/camera_namespace.inputs:value"), args.camera_namespace)
        _set_enabled(og.Controller, f"{robot_prim_path}/left_hawk/left_camera_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/left_hawk/right_camera_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/right_hawk/left_camera_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/right_hawk/right_camera_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/back_hawk/left_camera_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/back_hawk/right_camera_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/ros_lidars/front_2d_lidar_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/ros_lidars/back_2d_lidar_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/ros_lidars/front_3d_lidar_render_product", False)
        _set_enabled(og.Controller, f"{robot_prim_path}/front_hawk/left_camera_render_product", True)
        _set_enabled(og.Controller, f"{robot_prim_path}/front_hawk/right_camera_render_product", True)

        stage = omni.usd.get_context().get_stage()
        checkerboard_prim = stage.GetPrimAtPath(checkerboard_prim_path)
        xformable = UsdGeom.Xformable(checkerboard_prim)
        xformable.ClearXformOpOrder()

        chassis_position, chassis_orientation = get_world_pose(f"{robot_prim_path}/chassis_link")
        chassis_position = np.asarray(chassis_position, dtype=np.float64)
        chassis_orientation = np.asarray(chassis_orientation, dtype=np.float64)  # x y z w
        chassis_quat = Gf.Quatd(float(chassis_orientation[3]), Gf.Vec3d(*chassis_orientation[:3]))
        rotation = Gf.Rotation(chassis_quat)
        local_translation = np.array([args.board_x_m, args.board_y_m, args.board_z_m], dtype=np.float64)
        world_translation = chassis_position + np.asarray(rotation.TransformDir(Gf.Vec3d(*local_translation)), dtype=np.float64)

        board_local_quat = _euler_xyz_to_quaternion(
            np.deg2rad(float(args.board_roll_deg)),
            np.deg2rad(float(args.board_pitch_deg)),
            np.deg2rad(float(args.board_yaw_deg)),
        )
        board_local_quat_gf = Gf.Quatd(float(board_local_quat[3]), Gf.Vec3d(*board_local_quat[:3]))
        board_world_quat = chassis_quat * board_local_quat_gf

        xformable.AddTranslateOp().Set(Gf.Vec3d(*world_translation.tolist()))
        xformable.AddOrientOp().Set(board_world_quat)

        bbox_cache = UsdGeom.BBoxCache(0.0, [UsdGeom.Tokens.default_], useExtentsHint=True)
        board_bound = bbox_cache.ComputeWorldBound(checkerboard_prim).ComputeAlignedRange()
        board_size = np.array(board_bound.GetSize(), dtype=np.float64)

        square_cols = int(args.board_square_cols)
        square_rows = int(args.board_square_rows)
        payload = {
            "checkerboard_prim_path": checkerboard_prim_path,
            "chassis_link_pose_world": {
                "translation": chassis_position.tolist(),
                "quaternion_xyzw": chassis_orientation.tolist(),
            },
            "board_pose_world": {
                "translation": world_translation.tolist(),
                "quaternion_xyzw": [
                    float(board_world_quat.GetImaginary()[0]),
                    float(board_world_quat.GetImaginary()[1]),
                    float(board_world_quat.GetImaginary()[2]),
                    float(board_world_quat.GetReal()),
                ],
            },
            "board_pose_chassis": {
                "translation": local_translation.tolist(),
                "quaternion_xyzw": board_local_quat.tolist(),
            },
            "board_bbox_world_size_m": {
                "x": float(board_size[0]),
                "y": float(board_size[1]),
                "z": float(board_size[2]),
            },
            "board_square_cols": square_cols,
            "board_square_rows": square_rows,
            "board_inner_cols": square_cols - 1,
            "board_inner_rows": square_rows - 1,
        }
        board_meta_path = Path(args.board_meta_json)
        board_meta_path.parent.mkdir(parents=True, exist_ok=True)
        board_meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        simulation_context = SimulationContext(stage_units_in_meters=1.0)
        simulation_context.play()

        while app.is_running() and not stop_requested:
            simulation_context.step(render=True)

        simulation_context.stop()
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
