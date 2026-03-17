#!/usr/bin/env python3
"""Wait until the GS4 Isaac front-stereo runtime contract is materially ready."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_frame_idx(runtime_dir: Path) -> int | None:
    for candidate in ("worker_state.json", "isaac_timing.json"):
        payload = load_json(runtime_dir / candidate)
        value = payload.get("frame_idx")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
    return None


def runtime_ready(runtime_dir: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    camera_info = load_json(runtime_dir / "camera_info.json")
    stereo = dict(camera_info.get("isaac_front_stereo", {}) or {})
    if not bool(stereo.get("enabled", False)):
        issues.append("camera_info.json missing isaac_front_stereo.enabled=true")
    left_meta = dict(stereo.get("left", {}) or {})
    right_meta = dict(stereo.get("right", {}) or {})
    left_path = Path(str(left_meta.get("live_frame_path") or runtime_dir / "live_frames" / "rgb.png"))
    right_path = Path(str(right_meta.get("live_frame_path") or runtime_dir / "live_frames" / "rgb_right.png"))
    for label, path in (("left", left_path), ("right", right_path)):
        if not path.is_file():
            issues.append(f"{label} live frame missing: {path}")
            continue
        if path.stat().st_size <= 0:
            issues.append(f"{label} live frame empty: {path}")
    return (not issues, issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-dir", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument(
        "--min-frame-idx",
        type=int,
        default=0,
        help="Require worker_state/isaac_timing frame_idx to reach at least this value.",
    )
    parser.add_argument(
        "--require-frame-progress",
        type=int,
        default=0,
        help="Require this many frame_idx increments after the stereo contract looks ready.",
    )
    parser.add_argument(
        "--progress-interval-seconds",
        type=float,
        default=0.5,
        help="Polling interval used when requiring frame progress.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime_dir = Path(args.runtime_dir).expanduser().resolve()
    deadline = time.monotonic() + max(args.timeout_seconds, 0.1)
    last_issues: list[str] = ["runtime not checked"]
    last_frame_idx: int | None = None
    progress_hits = 0
    min_frame_idx = max(int(args.min_frame_idx), 0)
    required_progress = max(int(args.require_frame_progress), 0)
    progress_sleep_s = max(float(args.progress_interval_seconds), 0.1)
    while time.monotonic() <= deadline:
        ready, last_issues = runtime_ready(runtime_dir)
        if ready:
            if required_progress <= 0:
                frame_idx = load_frame_idx(runtime_dir)
                if min_frame_idx <= 0:
                    return 0
                if frame_idx is None:
                    last_issues = ["runtime contract ready but worker_state/isaac_timing frame_idx is unavailable"]
                elif frame_idx >= min_frame_idx:
                    return 0
                else:
                    last_issues = [
                        f"runtime contract ready but frame_idx={frame_idx} has not reached min_frame_idx={min_frame_idx}"
                    ]
                    last_frame_idx = frame_idx
                    progress_hits = 0
                    time.sleep(progress_sleep_s)
                    continue
            frame_idx = load_frame_idx(runtime_dir)
            if frame_idx is None:
                last_issues = ["runtime contract ready but worker_state/isaac_timing frame_idx is unavailable"]
            elif frame_idx < min_frame_idx:
                last_issues = [
                    f"runtime contract ready but frame_idx={frame_idx} has not reached min_frame_idx={min_frame_idx}"
                ]
                last_frame_idx = frame_idx
                progress_hits = 0
            elif last_frame_idx is None:
                last_frame_idx = frame_idx
                progress_hits = 0
            elif frame_idx > last_frame_idx:
                progress_hits += 1
                last_frame_idx = frame_idx
                if progress_hits >= required_progress:
                    return 0
            else:
                last_issues = [
                    f"runtime contract ready but frame_idx is not advancing (frame_idx={frame_idx}, progress_hits={progress_hits}/{required_progress})"
                ]
        else:
            last_frame_idx = None
            progress_hits = 0
        time.sleep(progress_sleep_s if required_progress > 0 else 0.2)
    print("\n".join(last_issues), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
