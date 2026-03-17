from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from semantic_mapper_pkg.io import load_fixture
from semantic_mapper_pkg.map_builder import SemanticMapBuilder
from semantic_mapper_pkg.runtime import export_query_results


def simulate_semantic_exploration(
    *,
    fixture_path: str | Path,
    output_map_path: str | Path,
    progress_output_path: str | Path,
    query_output_dir: str | Path,
    query_labels: list[str],
    merge_distance_m: float = 0.75,
) -> dict[str, object]:
    frames = load_fixture(fixture_path)
    ordered_steps = build_semantic_gain_route(frames)

    builder = SemanticMapBuilder(merge_distance_m=merge_distance_m)
    progress_steps: list[dict[str, object]] = []
    total_distance_m = 0.0

    for step_index, step in enumerate(ordered_steps):
        frame = step["frame"]
        before = builder.export()
        before_labels = set(before["labels"].keys())
        builder.add_frame(frame)
        after = builder.export()
        after_labels = set(after["labels"].keys())

        total_distance_m += float(step["distance_from_previous_m"])
        progress_steps.append(
            {
                "step_index": step_index,
                "frame_id": frame.frame_id,
                "pose": {
                    "x": round(frame.pose.x, 4),
                    "y": round(frame.pose.y, 4),
                    "z": round(frame.pose.z, 4),
                    "yaw": round(frame.pose.yaw, 4),
                },
                "distance_from_previous_m": round(float(step["distance_from_previous_m"]), 4),
                "planner_score": round(float(step["planner_score"]), 4),
                "detections": [detection.label for detection in frame.detections],
                "new_labels": sorted(after_labels - before_labels),
                "new_object_count": after["object_count"] - before["object_count"],
                "object_count_after": after["object_count"],
            }
        )

    output_map_path = Path(output_map_path)
    progress_output_path = Path(progress_output_path)
    output_map_path.parent.mkdir(parents=True, exist_ok=True)
    progress_output_path.parent.mkdir(parents=True, exist_ok=True)

    builder.export_to_path(output_map_path)
    query_paths = export_query_results(builder, query_labels, query_output_dir)

    payload = {
        "mode": "offline_semantic_exploration",
        "strategy": "semantic_gain_greedy",
        "fixture_path": str(Path(fixture_path)),
        "steps": progress_steps,
        "total_distance_m": round(total_distance_m, 4),
        "final_map_path": str(output_map_path),
        "query_outputs": [str(path) for path in query_paths],
        "final_map_summary": builder.export(),
    }
    progress_output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_semantic_gain_route(frames) -> list[dict[str, object]]:
    if not frames:
        return []

    unvisited = list(frames)
    current = unvisited.pop(0)
    seen_labels = {detection.label for detection in current.detections}
    route = [
        {
            "frame": current,
            "planner_score": semantic_gain_score(current, seen_labels=set()),
            "distance_from_previous_m": 0.0,
        }
    ]

    while unvisited:
        best_index = 0
        best_score = -1.0e12
        best_distance = 0.0

        for index, candidate in enumerate(unvisited):
            distance_m = pose_distance(current, candidate)
            score = semantic_gain_score(candidate, seen_labels=seen_labels) - (0.35 * distance_m)
            if score > best_score:
                best_index = index
                best_score = score
                best_distance = distance_m

        current = unvisited.pop(best_index)
        seen_labels.update(detection.label for detection in current.detections)
        route.append(
            {
                "frame": current,
                "planner_score": best_score,
                "distance_from_previous_m": best_distance,
            }
        )

    return route


def semantic_gain_score(frame, *, seen_labels: set[str]) -> float:
    labels = [detection.label for detection in frame.detections]
    unseen_labels = {label for label in labels if label not in seen_labels}
    return (2.0 * len(unseen_labels)) + (0.25 * len(labels))


def pose_distance(frame_a, frame_b) -> float:
    return math.dist(
        (frame_a.pose.x, frame_a.pose.y, frame_a.pose.z),
        (frame_b.pose.x, frame_b.pose.y, frame_b.pose.z),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline exploration scaffold that grows a semantic map while visiting candidate viewpoints."
    )
    parser.add_argument("--fixture", required=True, help="Path to the exploration fixture JSON.")
    parser.add_argument("--output-map", required=True, help="Path to the final semantic map JSON.")
    parser.add_argument("--output-progress", required=True, help="Path to the exploration progress JSON.")
    parser.add_argument("--query-output-dir", required=True, help="Directory for exported query JSON files.")
    parser.add_argument("--query-label", action="append", default=[], help="Query label to export.")
    parser.add_argument("--merge-distance", type=float, default=0.8, help="Merge distance in meters.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = simulate_semantic_exploration(
        fixture_path=args.fixture,
        output_map_path=args.output_map,
        progress_output_path=args.output_progress,
        query_output_dir=args.query_output_dir,
        query_labels=args.query_label,
        merge_distance_m=args.merge_distance,
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
