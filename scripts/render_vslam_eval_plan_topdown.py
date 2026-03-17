#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from isaacsim import SimulationApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the Office + Nova VSLAM eval path over the raw Isaac occupancy buffer."
    )
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--output-png", required=True)
    parser.add_argument("--output-svg", required=True)
    parser.add_argument("--output-json", default="")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--warmup-frames", type=int, default=60)
    return parser.parse_args()


def load_plan(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_figure(
    *,
    raw_buffer: np.ndarray,
    origin_xy: tuple[float, float],
    resolution_m: float,
    waypoints_world: list[dict],
    output_png: Path,
    output_svg: Path,
) -> dict[str, float | int]:
    free_mask = raw_buffer == 5
    occupied_mask = raw_buffer == 4
    unknown_mask = ~(free_mask | occupied_mask)

    width_px = raw_buffer.shape[1]
    height_px = raw_buffer.shape[0]
    min_x = float(origin_xy[0])
    min_y = float(origin_xy[1])
    max_x = min_x + width_px * resolution_m
    max_y = min_y + height_px * resolution_m

    canvas = np.full((height_px, width_px, 3), 0.92, dtype=np.float32)
    canvas[free_mask] = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    canvas[occupied_mask] = np.array([0.08, 0.08, 0.08], dtype=np.float32)
    canvas[unknown_mask] = np.array([0.72, 0.76, 0.80], dtype=np.float32)

    path_xy = np.array([[float(p["x"]), float(p["y"])] for p in waypoints_world], dtype=np.float64)

    fig, ax = plt.subplots(figsize=(10, 10), dpi=160)
    ax.imshow(canvas, origin="lower", extent=(min_x, max_x, min_y, max_y))
    ax.plot(path_xy[:, 0], path_xy[:, 1], color="#137CBD", linewidth=2.5, label="planned path")
    ax.scatter(path_xy[:, 0], path_xy[:, 1], s=44, color="#137CBD", zorder=3)
    ax.scatter(path_xy[0, 0], path_xy[0, 1], s=90, color="#0F9960", marker="o", zorder=4, label="start")
    ax.scatter(path_xy[-1, 0], path_xy[-1, 1], s=90, color="#DB3737", marker="X", zorder=4, label="goal")

    for index, point in enumerate(path_xy):
        ax.text(point[0] + 0.15, point[1] + 0.15, str(index), fontsize=9, color="#102A43")

    ax.set_title("AgentSlam Office + Nova VSLAM Benchmark Plan", fontsize=14)
    ax.set_xlabel("world x (m)")
    ax.set_ylabel("world y (m)")
    ax.legend(loc="upper right")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, color="#CED9E0", linewidth=0.5, alpha=0.5)
    fig.tight_layout()

    output_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_png, bbox_inches="tight")
    fig.savefig(output_svg, bbox_inches="tight")
    plt.close(fig)

    return {
        "occupied_pixels": int(np.count_nonzero(occupied_mask)),
        "free_pixels": int(np.count_nonzero(free_mask)),
        "unknown_pixels": int(np.count_nonzero(unknown_mask)),
        "map_width_px": int(width_px),
        "map_height_px": int(height_px),
    }


def main() -> int:
    args = parse_args()
    plan = load_plan(Path(args.plan_json))

    app = SimulationApp({"headless": args.headless, "disable_viewport_updates": args.headless})
    try:
        import omni.physx
        import omni.usd
        from isaacsim.asset.gen.omap.bindings import _omap
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading, open_stage
        from pxr import Sdf, UsdPhysics

        scene_path = str(Path(plan["scene_path"]).resolve())
        robot_path = str(Path(plan["robot_path"]).resolve())
        robot_prim_path = str(plan["robot_prim_path"])
        cell_size_m = float(plan["cell_size_m"])
        origin = plan["occupancy_origin_world"]
        width_px = int(plan["occupancy_dimensions_px"]["width"])
        height_px = int(plan["occupancy_dimensions_px"]["height"])
        min_xy = np.array([float(origin["x"]), float(origin["y"])], dtype=np.float64)
        max_xy = min_xy + np.array([width_px * cell_size_m, height_px * cell_size_m], dtype=np.float64)

        open_stage(scene_path)
        app.update()
        app.update()
        while is_stage_loading():
            app.update()

        add_reference_to_stage(robot_path, robot_prim_path)
        for _ in range(max(1, int(args.warmup_frames))):
            app.update()

        stage = omni.usd.get_context().get_stage()
        if not stage.GetPrimAtPath("/World/physicsScene").IsValid():
            UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))
            app.update()

        simulation_context = SimulationContext(stage_units_in_meters=1.0)
        simulation_context.play()
        for _ in range(10):
            simulation_context.step(render=False)

        physx = omni.physx.get_physx_interface()
        generator = _omap.Generator(physx, omni.usd.get_context().get_stage_id())
        generator.update_settings(cell_size_m, 4, 5, 6)
        generator.set_transform(
            (0.0, 0.0, 0.0),
            (float(min_xy[0]), float(min_xy[1]), 0.0),
            (float(max_xy[0]), float(max_xy[1]), 0.0),
        )
        generator.generate2d()
        dims = generator.get_dimensions()
        raw = np.array(generator.get_buffer(), dtype=np.uint8).reshape((int(dims[1]), int(dims[0])))

        summary = render_figure(
            raw_buffer=raw,
            origin_xy=(float(min_xy[0]), float(min_xy[1])),
            resolution_m=cell_size_m,
            waypoints_world=plan["waypoints_world"],
            output_png=Path(args.output_png),
            output_svg=Path(args.output_svg),
        )
        summary.update(
            {
                "plan_json": str(Path(args.plan_json).resolve()),
                "planned_length_m": float(plan["planned_length_m"]),
                "planned_turn_count": int(plan["planned_turn_count"]),
            }
        )

        if args.output_json:
            output_json = Path(args.output_json)
            output_json.parent.mkdir(parents=True, exist_ok=True)
            output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        simulation_context.stop()
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
