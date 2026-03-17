from __future__ import annotations

import argparse
import json
from pathlib import Path

from isaacsim import SimulationApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate that the local Isaac Office + Nova assets load together.")
    parser.add_argument("--scene", required=True, help="Absolute path to office stage USD.")
    parser.add_argument("--robot", required=True, help="Absolute path to Nova Carter USD.")
    parser.add_argument("--robot-prim-path", default="/World/NovaCarter")
    parser.add_argument("--output-json", help="Optional path to write validation summary JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = SimulationApp({"headless": True, "disable_viewport_updates": True})

    try:
        import omni
        from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading, open_stage

        scene_path = str(Path(args.scene).resolve())
        robot_path = str(Path(args.robot).resolve())

        open_stage(scene_path)
        app.update()
        app.update()
        while is_stage_loading():
            app.update()

        add_reference_to_stage(robot_path, args.robot_prim_path)
        for _ in range(5):
            app.update()

        stage = omni.usd.get_context().get_stage()
        robot_prim = stage.GetPrimAtPath(args.robot_prim_path) if stage else None
        summary = {
            "scene_path": scene_path,
            "robot_path": robot_path,
            "robot_prim_path": args.robot_prim_path,
            "stage_loaded": stage is not None,
            "robot_prim_valid": bool(robot_prim and robot_prim.IsValid()),
            "default_prim": str(stage.GetDefaultPrim().GetPath()) if stage and stage.GetDefaultPrim() else None,
        }
        if args.output_json:
            Path(args.output_json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        if not summary["stage_loaded"] or not summary["robot_prim_valid"]:
            return 1
        return 0
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
