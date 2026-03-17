#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render an offline exploration semantic map visualization."
    )
    parser.add_argument("--map", required=True, help="Path to exploration_semantic_map.json")
    parser.add_argument(
        "--progress",
        required=True,
        help="Path to exploration_progress.json",
    )
    parser.add_argument("--output-png", required=True, help="Path to output PNG")
    parser.add_argument("--output-svg", required=True, help="Path to output SVG")
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def render_plot(map_payload: dict, progress_payload: dict, output_png: Path, output_svg: Path) -> None:
    objects = map_payload.get("objects", [])
    steps = progress_payload.get("steps", [])

    fig, ax = plt.subplots(figsize=(10, 7))

    route_x = [step["pose"]["x"] for step in steps]
    route_y = [step["pose"]["y"] for step in steps]
    if route_x and route_y:
        ax.plot(
            route_x,
            route_y,
            color="#355C7D",
            linewidth=2.2,
            marker="o",
            markersize=7,
            label="Exploration route",
            zorder=2,
        )
        for step in steps:
            ax.annotate(
                f'{step["step_index"]}:{step["frame_id"]}',
                (step["pose"]["x"], step["pose"]["y"]),
                textcoords="offset points",
                xytext=(6, 8),
                fontsize=8,
                color="#1F2A44",
            )

    if objects:
        palette = [
            "#D1495B",
            "#00798C",
            "#EDAe49",
            "#30638E",
            "#6A994E",
            "#9C6644",
            "#5C4D7D",
            "#BC4B51",
        ]
        label_to_color: dict[str, str] = {}
        for index, label in enumerate(sorted({obj["label"] for obj in objects})):
            label_to_color[label] = palette[index % len(palette)]

        for obj in objects:
            position = obj["position"]
            label = obj["label"]
            ax.scatter(
                position["x"],
                position["y"],
                s=170,
                color=label_to_color[label],
                edgecolors="black",
                linewidths=0.6,
                alpha=0.9,
                zorder=3,
            )
            ax.annotate(
                f'{label} ({obj["observation_count"]})',
                (position["x"], position["y"]),
                textcoords="offset points",
                xytext=(6, -14),
                fontsize=8,
                color="#111111",
            )

        handles = [
            plt.Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=color,
                markeredgecolor="black",
                markersize=9,
                label=label,
            )
            for label, color in label_to_color.items()
        ]
        route_handle = plt.Line2D(
            [0],
            [0],
            color="#355C7D",
            marker="o",
            linewidth=2.2,
            markersize=7,
            label="Exploration route",
        )
        ax.legend(handles=[route_handle, *handles], loc="upper left", frameon=True)

    ax.set_title("Phase 1 Exploration-Backed Semantic Map", fontsize=14, pad=12)
    ax.set_xlabel("World X (m)")
    ax.set_ylabel("World Y (m)")
    ax.grid(True, linestyle="--", alpha=0.25)
    ax.set_aspect("equal", adjustable="box")

    summary = progress_payload.get("final_map_summary", {})
    total_distance = progress_payload.get("total_distance_m", 0.0)
    object_count = summary.get("object_count", 0)
    ax.text(
        0.99,
        0.01,
        f"Objects: {object_count}\nRoute distance: {total_distance} m\nSteps: {len(steps)}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.85, "edgecolor": "#CCCCCC"},
    )

    output_png.parent.mkdir(parents=True, exist_ok=True)
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_png, dpi=180)
    fig.savefig(output_svg)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    map_payload = load_json(args.map)
    progress_payload = load_json(args.progress)
    render_plot(
        map_payload=map_payload,
        progress_payload=progress_payload,
        output_png=Path(args.output_png),
        output_svg=Path(args.output_svg),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
