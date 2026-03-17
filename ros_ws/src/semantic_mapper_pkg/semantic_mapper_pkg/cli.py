from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import load_fixture
from .map_builder import SemanticMapBuilder
from .runtime import export_query_results, load_exported_map, query_exported_map


def build_map_from_fixture(fixture_path: str | Path, output_path: str | Path, merge_distance_m: float) -> dict[str, object]:
    builder = SemanticMapBuilder(merge_distance_m=merge_distance_m)
    for frame in load_fixture(fixture_path):
        builder.add_frame(frame)
    builder.export_to_path(output_path)
    return builder.export()


def run_fixture_main() -> int:
    parser = argparse.ArgumentParser(description="Build a semantic map from an offline fixture.")
    parser.add_argument("--fixture", required=True, help="Path to the synthetic or replay fixture JSON.")
    parser.add_argument("--output", required=True, help="Path to write the exported semantic map JSON.")
    parser.add_argument("--merge-distance", type=float, default=0.75, help="Merge distance in meters.")
    args = parser.parse_args()

    result = build_map_from_fixture(
        fixture_path=args.fixture,
        output_path=args.output,
        merge_distance_m=args.merge_distance,
    )
    print(json.dumps(result, indent=2))
    return 0


def run_query_main() -> int:
    parser = argparse.ArgumentParser(
        description="Query a semantic map export by label substring with optional spatial filters."
    )
    parser.add_argument("--map", required=True, help="Path to the exported semantic map JSON.")
    parser.add_argument("--label", required=True, help="Label or partial label to search for.")
    parser.add_argument("--near-x", type=float, help="Optional query reference x position in meters.")
    parser.add_argument("--near-y", type=float, help="Optional query reference y position in meters.")
    parser.add_argument("--radius-m", type=float, help="Optional radial filter around the reference point.")
    parser.add_argument(
        "--min-observations",
        type=int,
        default=1,
        help="Require each returned object to have at least this many observations.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of matches to return. Use 0 for no limit.",
    )
    parser.add_argument(
        "--output",
        help="Optional path to also write the query response JSON.",
    )
    args = parser.parse_args()

    payload = load_exported_map(args.map)
    response = query_exported_map(
        payload,
        args.label,
        near_x=args.near_x,
        near_y=args.near_y,
        radius_m=args.radius_m,
        min_observations=args.min_observations,
        limit=args.limit,
    )
    if args.output:
        Path(args.output).write_text(json.dumps(response, indent=2), encoding="utf-8")
    print(json.dumps(response, indent=2))
    return 0


def run_fixture_with_queries_main() -> int:
    parser = argparse.ArgumentParser(description="Build a semantic map from fixture and export query JSON files.")
    parser.add_argument("--fixture", required=True, help="Path to the fixture JSON.")
    parser.add_argument("--output", required=True, help="Path to write the exported semantic map JSON.")
    parser.add_argument("--query-output-dir", required=True, help="Directory for query result JSON files.")
    parser.add_argument("--query-label", action="append", default=[], help="Query label to export.")
    parser.add_argument("--merge-distance", type=float, default=0.75, help="Merge distance in meters.")
    args = parser.parse_args()

    builder = SemanticMapBuilder(merge_distance_m=args.merge_distance)
    for frame in load_fixture(args.fixture):
        builder.add_frame(frame)
    builder.export_to_path(args.output)
    query_paths = export_query_results(builder, args.query_label, args.query_output_dir)
    response = {
        "map_output": str(Path(args.output)),
        "query_outputs": [str(path) for path in query_paths],
        "map": builder.export(),
    }
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_fixture_main())
