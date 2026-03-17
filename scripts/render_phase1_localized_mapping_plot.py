#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render localized occupancy and semantic mapping artifacts into static plots."
    )
    parser.add_argument("--occupancy", required=True, help="Path to localized occupancy JSON.")
    parser.add_argument("--semantic", required=True, help="Path to localized semantic map JSON.")
    parser.add_argument("--overview-png", required=True, help="Output PNG path for the overview plot.")
    parser.add_argument("--overview-svg", required=True, help="Output SVG path for the overview plot.")
    parser.add_argument("--grid-png", required=True, help="Output PNG path for the occupancy-only plot.")
    parser.add_argument("--grid-svg", required=True, help="Output SVG path for the occupancy-only plot.")
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def draw_occupancy_cells(ax: plt.Axes, occupancy: dict, *, alpha: float = 0.95) -> None:
    resolution = float(occupancy["resolution_m"])

    for cell in occupancy.get("free_cells", []):
        world = cell["world"]
        rect = patches.Rectangle(
            (world["x"] - resolution / 2.0, world["y"] - resolution / 2.0),
            resolution,
            resolution,
            facecolor="#E7F0D8",
            edgecolor="#D6E4C3",
            linewidth=0.5,
            alpha=0.8 * alpha,
            zorder=1,
        )
        ax.add_patch(rect)

    for cell in occupancy.get("occupied_cells", []):
        world = cell["world"]
        score = float(cell.get("score", 0))
        color = "#A61E4D" if score >= 4 else "#D9485F"
        rect = patches.Rectangle(
            (world["x"] - resolution / 2.0, world["y"] - resolution / 2.0),
            resolution,
            resolution,
            facecolor=color,
            edgecolor="#7C1D32",
            linewidth=0.7,
            alpha=alpha,
            zorder=2,
        )
        ax.add_patch(rect)


def draw_path(ax: plt.Axes, occupancy: dict) -> None:
    path = occupancy.get("path", [])
    if not path:
        return

    xs = [step["x"] for step in path]
    ys = [step["y"] for step in path]
    ax.plot(
        xs,
        ys,
        color="#355C7D",
        linewidth=2.6,
        marker="o",
        markersize=7,
        label="Robot path",
        zorder=4,
    )
    for index, step in enumerate(path):
        ax.annotate(
            f'{index}:{step["frame_id"]}',
            (step["x"], step["y"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8,
            color="#1F2A44",
            zorder=5,
        )


def draw_observed_points(ax: plt.Axes, occupancy: dict) -> None:
    points = occupancy.get("observed_points", [])
    if not points:
        return
    xs = [point["x"] for point in points]
    ys = [point["y"] for point in points]
    ax.scatter(
        xs,
        ys,
        marker="x",
        s=50,
        color="#6C757D",
        alpha=0.8,
        label="Observed rays",
        zorder=3,
    )


def draw_semantic_objects(ax: plt.Axes, semantic: dict) -> None:
    objects = semantic.get("objects", [])
    if not objects:
        return

    palette = {
        "chair": "#0B7285",
        "desk": "#F08C00",
        "cabinet": "#C2255C",
        "table": "#8D6E63",
        "plant": "#5C940D",
        "sofa": "#7B2CBF",
    }

    for obj in objects:
        pos = obj["position"]
        label = obj["label"]
        color = palette.get(label, "#495057")
        ax.scatter(
            pos["x"],
            pos["y"],
            s=190,
            color=color,
            edgecolors="black",
            linewidths=0.7,
            alpha=0.95,
            zorder=6,
        )
        ax.annotate(
            f'{label} ({obj["observation_count"]})',
            (pos["x"], pos["y"]),
            textcoords="offset points",
            xytext=(7, -13),
            fontsize=8,
            color="#111111",
            zorder=7,
        )


def finalize_axes(ax: plt.Axes, occupancy: dict, title: str) -> None:
    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel("World X (m)")
    ax.set_ylabel("World Y (m)")
    ax.grid(True, linestyle="--", alpha=0.2)
    ax.set_aspect("equal", adjustable="box")

    width = float(occupancy["width"]) * float(occupancy["resolution_m"])
    height = float(occupancy["height"]) * float(occupancy["resolution_m"])
    origin = occupancy["origin"]
    margin = 0.35
    ax.set_xlim(origin["x"] - margin, origin["x"] + width + margin)
    ax.set_ylim(origin["y"] - margin, origin["y"] + height + margin)


def render_overview(occupancy: dict, semantic: dict, png_path: Path, svg_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    draw_occupancy_cells(ax, occupancy, alpha=0.65)
    draw_observed_points(ax, occupancy)
    draw_path(ax, occupancy)
    draw_semantic_objects(ax, semantic)
    finalize_axes(ax, occupancy, "AgentSlam Localized Mapping Overview")

    stats = (
        f'Objects: {semantic.get("object_count", 0)}\n'
        f'Occupied cells: {occupancy.get("occupied_count", 0)}\n'
        f'Free cells: {occupancy.get("free_count", 0)}\n'
        f'Steps: {len(occupancy.get("path", []))}'
    )
    ax.text(
        0.985,
        0.02,
        stats,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.88, "edgecolor": "#CCCCCC"},
        zorder=8,
    )

    fig.tight_layout()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=180)
    fig.savefig(svg_path)
    plt.close(fig)


def render_grid_only(occupancy: dict, png_path: Path, svg_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 7))
    draw_occupancy_cells(ax, occupancy, alpha=0.9)
    draw_path(ax, occupancy)
    finalize_axes(ax, occupancy, "AgentSlam Localized Occupancy Grid")

    fig.tight_layout()
    png_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=180)
    fig.savefig(svg_path)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    occupancy = load_json(args.occupancy)
    semantic = load_json(args.semantic)
    render_overview(
        occupancy,
        semantic,
        png_path=Path(args.overview_png),
        svg_path=Path(args.overview_svg),
    )
    render_grid_only(
        occupancy,
        png_path=Path(args.grid_png),
        svg_path=Path(args.grid_svg),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
