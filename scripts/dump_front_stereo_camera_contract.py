#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from isaacsim import SimulationApp


def invert_transform(transform: np.ndarray) -> np.ndarray:
    rotation = transform[:3, :3]
    translation = transform[:3, 3]
    inverse = np.eye(4, dtype=np.float64)
    inverse[:3, :3] = rotation.T
    inverse[:3, 3] = -rotation.T @ translation
    return inverse


def quaternion_wxyz_to_matrix(quat_wxyz: np.ndarray) -> np.ndarray:
    w, x, y, z = quat_wxyz
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


def make_transform(translation: np.ndarray, rotation: np.ndarray) -> np.ndarray:
    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation
    return transform


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dump actual Nova front stereo camera intrinsics and poses from Isaac Sim.")
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
    parser.add_argument("--resolution-width", type=int, default=1280)
    parser.add_argument("--resolution-height", type=int, default=720)
    parser.add_argument("--warmup-frames", type=int, default=45)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)

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
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading, open_stage
        from isaacsim.core.utils.xforms import get_world_pose
        from isaacsim.sensors.camera import Camera

        open_stage(args.scene)
        app.update()
        app.update()
        while is_stage_loading():
            app.update()

        add_reference_to_stage(args.robot, args.robot_prim_path)
        for _ in range(max(1, int(args.warmup_frames))):
            app.update()

        sim = SimulationContext(stage_units_in_meters=1.0)
        sim.play()
        for _ in range(5):
            sim.step(render=False)

        resolution = (int(args.resolution_width), int(args.resolution_height))
        left_camera = Camera(prim_path=args.left_camera_prim, name="left_contract_dump", resolution=resolution)
        right_camera = Camera(prim_path=args.right_camera_prim, name="right_contract_dump", resolution=resolution)
        left_camera.initialize()
        right_camera.initialize()

        left_intrinsics = np.asarray(left_camera.get_intrinsics_matrix(), dtype=np.float64)
        right_intrinsics = np.asarray(right_camera.get_intrinsics_matrix(), dtype=np.float64)
        left_world_t_camera_ros = invert_transform(np.asarray(left_camera.get_view_matrix_ros(), dtype=np.float64))
        right_world_t_camera_ros = invert_transform(np.asarray(right_camera.get_view_matrix_ros(), dtype=np.float64))
        chassis_position, chassis_quaternion_wxyz = get_world_pose(args.chassis_prim)
        world_t_chassis = make_transform(
            np.asarray(chassis_position, dtype=np.float64),
            quaternion_wxyz_to_matrix(np.asarray(chassis_quaternion_wxyz, dtype=np.float64)),
        )

        payload = {
            "scene": args.scene,
            "robot": args.robot,
            "resolution": {"width": int(args.resolution_width), "height": int(args.resolution_height)},
            "chassis_prim": args.chassis_prim,
            "left_camera": {
                "prim_path": args.left_camera_prim,
                "intrinsics_matrix": left_intrinsics.tolist(),
                "world_t_camera_ros": left_world_t_camera_ros.tolist(),
            },
            "right_camera": {
                "prim_path": args.right_camera_prim,
                "intrinsics_matrix": right_intrinsics.tolist(),
                "world_t_camera_ros": right_world_t_camera_ros.tolist(),
            },
            "world_t_chassis": world_t_chassis.tolist(),
        }
        output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        sim.stop()
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
