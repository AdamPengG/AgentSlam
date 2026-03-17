#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import traceback
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import isaacsim
from isaacsim import SimulationApp
from PIL import Image, ImageDraw


@dataclass
class Pose2D:
    x: float
    y: float
    yaw_rad: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a drivable long-route evaluation path for Office + Nova using Isaac Sim occupancy data."
    )
    parser.add_argument(
        "--scene",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd",
    )
    parser.add_argument(
        "--robot",
        default="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd",
    )
    parser.add_argument("--robot-prim-path", default="/World/NovaCarter")
    parser.add_argument("--robot-base-prim-path", default="/World/NovaCarter/chassis_link")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-map-dir", default="")
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--warmup-frames", type=int, default=60)
    parser.add_argument("--cell-size-m", type=float, default=0.10)
    parser.add_argument("--clearance-m", type=float, default=0.40)
    parser.add_argument("--target-length-m", type=float, default=20.0)
    parser.add_argument("--segment-target-length-m", type=float, default=5.0)
    parser.add_argument("--min-segment-length-m", type=float, default=3.5)
    parser.add_argument("--max-segment-length-m", type=float, default=7.0)
    parser.add_argument("--max-segments", type=int, default=4)
    parser.add_argument("--start-heading-rad", type=float, default=0.0)
    parser.add_argument("--max-start-heading-deg", type=float, default=45.0)
    parser.add_argument("--start-heading-penalty-weight", type=float, default=3.0)
    parser.add_argument("--min-turn-deg", type=float, default=35.0)
    parser.add_argument("--max-turn-deg", type=float, default=100.0)
    parser.add_argument("--path-length-tolerance-m", type=float, default=3.0)
    parser.add_argument("--min-turn-count", type=int, default=1)
    parser.add_argument("--max-turn-count", type=int, default=6)
    parser.add_argument("--sample-candidates", type=int, default=250)
    parser.add_argument("--max-goal-path-evals", type=int, default=48)
    parser.add_argument("--bounds-margin-m", type=float, default=1.0)
    parser.add_argument("--map-half-extent-m", type=float, default=15.0)
    parser.add_argument("--omap-origin-z-offset-m", type=float, default=0.0)
    parser.add_argument("--omap-z-min-m", type=float, default=-0.20)
    parser.add_argument("--omap-z-max-m", type=float, default=1.20)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def wrap_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def rotation_matrix(yaw_rad: float) -> np.ndarray:
    c = math.cos(yaw_rad)
    s = math.sin(yaw_rad)
    return np.array([[c, -s], [s, c]], dtype=np.float64)


def subtract_start_translation(point_xy: np.ndarray, origin: Pose2D) -> np.ndarray:
    return point_xy - np.array([origin.x, origin.y], dtype=np.float64)


def segment_length(points_xy: np.ndarray) -> float:
    if len(points_xy) < 2:
        return 0.0
    deltas = points_xy[1:] - points_xy[:-1]
    return float(np.sum(np.linalg.norm(deltas, axis=1)))


def count_turns(points_xy: np.ndarray, min_turn_rad: float) -> int:
    if len(points_xy) < 3:
        return 0
    turn_count = 0
    previous_heading: float | None = None
    for index in range(1, len(points_xy)):
        delta = points_xy[index] - points_xy[index - 1]
        if np.linalg.norm(delta) < 1e-6:
            continue
        heading = math.atan2(float(delta[1]), float(delta[0]))
        if previous_heading is not None and abs(wrap_angle(heading - previous_heading)) >= min_turn_rad:
            turn_count += 1
        previous_heading = heading
    return turn_count


def max_turn_angle(points_xy: np.ndarray) -> float:
    if len(points_xy) < 3:
        return 0.0
    previous_heading: float | None = None
    largest = 0.0
    for index in range(1, len(points_xy)):
        delta = points_xy[index] - points_xy[index - 1]
        if np.linalg.norm(delta) < 1e-6:
            continue
        heading = math.atan2(float(delta[1]), float(delta[0]))
        if previous_heading is not None:
            largest = max(largest, abs(wrap_angle(heading - previous_heading)))
        previous_heading = heading
    return largest


def initial_heading(points_xy: np.ndarray) -> float | None:
    if len(points_xy) < 2:
        return None
    delta = points_xy[1] - points_xy[0]
    if np.linalg.norm(delta) < 1e-6:
        return None
    return math.atan2(float(delta[1]), float(delta[0]))


def find_nearest_free_pixel(pixel_xy: np.ndarray, free_mask: np.ndarray) -> np.ndarray:
    x_px = int(np.clip(round(float(pixel_xy[0])), 0, free_mask.shape[1] - 1))
    y_px = int(np.clip(round(float(pixel_xy[1])), 0, free_mask.shape[0] - 1))
    if free_mask[y_px, x_px]:
        return np.array([x_px, y_px], dtype=np.int64)
    free_indices = np.argwhere(free_mask)
    if free_indices.size == 0:
        raise RuntimeError("occupancy map has no reachable free cells")
    distances = np.sum((free_indices - np.array([y_px, x_px])) ** 2, axis=1)
    nearest = free_indices[int(np.argmin(distances))]
    return np.array([int(nearest[1]), int(nearest[0])], dtype=np.int64)


def compress_path(path_xy: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    if len(path_xy) < 3:
        return path_xy
    keep = [0]
    for index in range(1, len(path_xy) - 1):
        prev_pt = path_xy[index - 1]
        curr_pt = path_xy[index]
        next_pt = path_xy[index + 1]
        v1 = curr_pt - prev_pt
        v2 = next_pt - curr_pt
        if np.linalg.norm(v1) < eps or np.linalg.norm(v2) < eps:
            continue
        direction_change = np.linalg.norm((v2 / np.linalg.norm(v2)) - (v1 / np.linalg.norm(v1)))
        if direction_change > 1e-3:
            keep.append(index)
    keep.append(len(path_xy) - 1)
    keep = sorted(set(keep))
    return path_xy[keep]


def save_debug_plan_topdown(
    *,
    raw_buffer: np.ndarray,
    origin_xy: np.ndarray,
    resolution_m: float,
    world_path: np.ndarray,
    output_png: Path,
    output_json: Path,
) -> None:
    free_mask = raw_buffer == 5
    occupied_mask = raw_buffer == 4
    unknown_mask = ~(free_mask | occupied_mask)

    height_px, width_px = raw_buffer.shape
    canvas = np.full((height_px, width_px, 3), 235, dtype=np.uint8)
    canvas[free_mask] = np.array([255, 255, 255], dtype=np.uint8)
    canvas[occupied_mask] = np.array([28, 28, 28], dtype=np.uint8)
    canvas[unknown_mask] = np.array([184, 194, 204], dtype=np.uint8)

    image = Image.fromarray(canvas, mode="RGB")
    draw = ImageDraw.Draw(image)

    def world_to_image(point_xy: np.ndarray) -> tuple[float, float]:
        x_px = (float(point_xy[0]) - float(origin_xy[0])) / resolution_m
        y_px = (float(point_xy[1]) - float(origin_xy[1])) / resolution_m
        return (x_px, float(height_px - 1) - y_px)

    pixel_path = [world_to_image(point_xy) for point_xy in world_path]
    if len(pixel_path) >= 2:
        draw.line(pixel_path, fill=(19, 124, 189), width=3)
    for index, pixel_xy in enumerate(pixel_path):
        radius = 4
        color = (15, 153, 96) if index == 0 else (219, 55, 55) if index == len(pixel_path) - 1 else (19, 124, 189)
        draw.ellipse(
            (
                pixel_xy[0] - radius,
                pixel_xy[1] - radius,
                pixel_xy[0] + radius,
                pixel_xy[1] + radius,
            ),
            fill=color,
        )

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png)
    output_json.write_text(
        json.dumps(
            {
                "occupied_pixels": int(np.count_nonzero(occupied_mask)),
                "free_pixels": int(np.count_nonzero(free_mask)),
                "unknown_pixels": int(np.count_nonzero(unknown_mask)),
                "path_waypoint_count": int(len(world_path)),
                "path_png": str(output_png),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def build_visual_mesh_bbox_occupancy(
    *,
    stage: object,
    bbox_cache: object,
    min_xy: np.ndarray,
    max_xy: np.ndarray,
    resolution_m: float,
    z_window_world: tuple[float, float],
) -> tuple[np.ndarray, dict[str, int]]:
    width_px = max(int(math.ceil((float(max_xy[0]) - float(min_xy[0])) / resolution_m)), 1)
    height_px = max(int(math.ceil((float(max_xy[1]) - float(min_xy[1])) / resolution_m)), 1)
    occupied_mask = np.zeros((height_px, width_px), dtype=bool)

    mesh_count = 0
    in_window_count = 0
    painted_count = 0
    skipped_outside_xy = 0
    skipped_outside_z = 0
    skipped_floor_like = 0

    z_min_world, z_max_world = z_window_world

    for prim in stage.Traverse():
        if prim.GetTypeName() != "Mesh":
            continue
        mesh_count += 1
        aligned = bbox_cache.ComputeWorldBound(prim).ComputeAlignedRange()
        bbox_min = np.array([float(value) for value in aligned.GetMin()], dtype=np.float64)
        bbox_max = np.array([float(value) for value in aligned.GetMax()], dtype=np.float64)

        if bbox_max[0] < min_xy[0] or bbox_min[0] > max_xy[0] or bbox_max[1] < min_xy[1] or bbox_min[1] > max_xy[1]:
            skipped_outside_xy += 1
            continue
        if bbox_max[2] < z_min_world or bbox_min[2] > z_max_world:
            skipped_outside_z += 1
            continue

        footprint_x = max(0.0, bbox_max[0] - bbox_min[0])
        footprint_y = max(0.0, bbox_max[1] - bbox_min[1])
        height_m = max(0.0, bbox_max[2] - bbox_min[2])
        footprint_area = footprint_x * footprint_y

        # Ignore floor-like slabs that would otherwise fill the whole map.
        is_robot_mesh = prim.GetPath().pathString.startswith("/World/NovaCarter/")
        if is_robot_mesh:
            continue

        if height_m <= 0.05 and bbox_max[2] <= z_min_world + 0.35 and footprint_area >= 1.0:
            skipped_floor_like += 1
            continue

        in_window_count += 1

        x0 = int(math.floor((bbox_min[0] - float(min_xy[0])) / resolution_m))
        x1 = int(math.ceil((bbox_max[0] - float(min_xy[0])) / resolution_m))
        y0 = int(math.floor((float(max_xy[1]) - bbox_max[1]) / resolution_m))
        y1 = int(math.ceil((float(max_xy[1]) - bbox_min[1]) / resolution_m))

        x0 = max(0, min(width_px - 1, x0))
        y0 = max(0, min(height_px - 1, y0))
        x1 = max(x0 + 1, min(width_px, x1))
        y1 = max(y0 + 1, min(height_px, y1))
        occupied_mask[y0:y1, x0:x1] = True
        painted_count += 1

    return occupied_mask, {
        "mesh_count": mesh_count,
        "meshes_in_xy_z_window": in_window_count,
        "meshes_painted": painted_count,
        "meshes_skipped_outside_xy": skipped_outside_xy,
        "meshes_skipped_outside_z": skipped_outside_z,
        "meshes_skipped_floor_like": skipped_floor_like,
    }


def line_is_free(
    occupancy_map: object,
    free_mask: np.ndarray,
    start_world_xy: np.ndarray,
    end_world_xy: np.ndarray,
) -> bool:
    start_px = occupancy_map.world_to_pixel_numpy(start_world_xy[None, :])[0]
    end_px = occupancy_map.world_to_pixel_numpy(end_world_xy[None, :])[0]
    pixel_distance = float(np.linalg.norm(end_px - start_px))
    samples = max(int(math.ceil(pixel_distance * 2.0)), 2)
    xs = np.linspace(float(start_px[0]), float(end_px[0]), samples)
    ys = np.linspace(float(start_px[1]), float(end_px[1]), samples)
    for x_px, y_px in zip(xs, ys):
        xi = int(np.clip(round(x_px), 0, free_mask.shape[1] - 1))
        yi = int(np.clip(round(y_px), 0, free_mask.shape[0] - 1))
        if not free_mask[yi, xi]:
            return False
    return True


def shortcut_path(occupancy_map: object, free_mask: np.ndarray, path_world: np.ndarray) -> np.ndarray:
    if len(path_world) < 3:
        return path_world

    simplified = [path_world[0]]
    anchor_index = 0
    while anchor_index < len(path_world) - 1:
        furthest_index = anchor_index + 1
        for candidate_index in range(anchor_index + 2, len(path_world)):
            if line_is_free(occupancy_map, free_mask, path_world[anchor_index], path_world[candidate_index]):
                furthest_index = candidate_index
            else:
                break
        simplified.append(path_world[furthest_index])
        anchor_index = furthest_index

    return np.array(simplified, dtype=np.float64)


def build_path_to_pixel(
    *,
    occupancy_map: object,
    free_mask: np.ndarray,
    output: object,
    goal_yx: np.ndarray,
    enable_shortcut: bool = True,
) -> np.ndarray | None:
    path_yx = output.unroll_path((int(goal_yx[0]), int(goal_yx[1])))
    if len(path_yx) < 2:
        return None
    path_xy = path_yx[:, ::-1].astype(np.float64)
    path_world = occupancy_map.pixel_to_world_numpy(path_xy)
    if enable_shortcut:
        path_world = shortcut_path(occupancy_map, free_mask, path_world)
    path_world = compress_path(path_world)
    return path_world


def choose_goal_path(
    *,
    occupancy_map: object,
    path_planner: object,
    start_world_xy: np.ndarray,
    target_length_m: float,
    path_length_tolerance_m: float,
    desired_start_heading_rad: float,
    max_start_heading_deviation_rad: float,
    min_turn_rad: float,
    max_turn_rad: float,
    min_turn_count: int,
    max_turn_count: int,
    heading_penalty_weight: float,
    sample_candidates: int,
    max_goal_path_evals: int,
    distance_resolution_m: float,
    log_fn=None,
) -> tuple[np.ndarray, dict[str, float]] | None:
    free_mask = occupancy_map.buffered_meters(0.0).freespace_mask()
    start_px_xy = find_nearest_free_pixel(occupancy_map.world_to_pixel_numpy(start_world_xy[None, :])[0], free_mask)
    start_tuple = (int(start_px_xy[1]), int(start_px_xy[0]))
    output = path_planner.generate_paths(start_tuple, free_mask)
    visited_indices = np.argwhere(output.visited != 0)
    if visited_indices.size == 0:
        return None

    distance_map = np.asarray(output.distance_to_start, dtype=np.float64)
    candidate_distances = distance_map[visited_indices[:, 0], visited_indices[:, 1]] * float(distance_resolution_m)
    valid_mask = np.isfinite(candidate_distances) & (candidate_distances > 0.0)
    visited_indices = visited_indices[valid_mask]
    candidate_distances = candidate_distances[valid_mask]
    if visited_indices.size == 0:
        return None

    min_length = max(0.0, target_length_m - path_length_tolerance_m)
    max_length = target_length_m + path_length_tolerance_m
    geodesic_lower = max(min_length, target_length_m * 0.65)
    geodesic_upper = max_length * 1.8
    geodesic_mask = (candidate_distances >= geodesic_lower) & (candidate_distances <= geodesic_upper)
    if np.any(geodesic_mask):
        visited_indices = visited_indices[geodesic_mask]
        candidate_distances = candidate_distances[geodesic_mask]

    if log_fn is not None:
        log_fn(
            "planner: goal search candidates="
            f"{int(np.sum(valid_mask))} filtered={len(visited_indices)} "
            f"geodesic_range=({geodesic_lower:.2f}, {geodesic_upper:.2f})"
        )

    endpoint_world = occupancy_map.pixel_to_world_numpy(visited_indices[:, ::-1].astype(np.float64))
    endpoint_vectors = endpoint_world - start_world_xy[None, :]
    endpoint_headings = np.arctan2(endpoint_vectors[:, 1], endpoint_vectors[:, 0])
    heading_deltas = np.abs(np.arctan2(
        np.sin(endpoint_headings - desired_start_heading_rad),
        np.cos(endpoint_headings - desired_start_heading_rad),
    ))
    ranking = np.abs(candidate_distances - target_length_m) + heading_penalty_weight * heading_deltas
    shortlist_size = max(8, min(int(max_goal_path_evals), len(visited_indices)))
    shortlist_ids = np.argsort(ranking)[:shortlist_size]
    visited_indices = visited_indices[shortlist_ids]
    candidate_distances = candidate_distances[shortlist_ids]

    if sample_candidates > 0 and len(visited_indices) > sample_candidates:
        rng = np.random.default_rng(len(visited_indices) + int(start_px_xy[0]) + int(start_px_xy[1]))
        sample_ids = rng.choice(len(visited_indices), size=sample_candidates, replace=False)
        visited_indices = visited_indices[sample_ids]
        candidate_distances = candidate_distances[sample_ids]
    if log_fn is not None:
        log_fn(f"planner: goal search shortlist={len(visited_indices)}")

    best_score = -1e18
    best_path: np.ndarray | None = None
    best_goal: dict[str, float] | None = None
    relaxed_score = -1e18
    relaxed_path: np.ndarray | None = None
    relaxed_goal: dict[str, float] | None = None

    for candidate_yx, geodesic_length_m in zip(visited_indices, candidate_distances):
        path_world = build_path_to_pixel(
            occupancy_map=occupancy_map,
            free_mask=free_mask,
            output=output,
            goal_yx=candidate_yx,
            enable_shortcut=False,
        )
        if path_world is None:
            continue
        length_m = segment_length(path_world)
        heading = initial_heading(path_world)
        if heading is None:
            continue
        heading_delta = abs(wrap_angle(heading - desired_start_heading_rad))
        turn_count = count_turns(path_world, min_turn_rad)
        largest_turn = max_turn_angle(path_world)
        geodesic_bonus = -0.05 * abs(float(geodesic_length_m) - target_length_m)
        relaxed_turn_penalty = 0.1 * abs(turn_count - min(max(turn_count, min_turn_count), max_turn_count))
        relaxed_largest_turn_penalty = 0.05 * max(0.0, largest_turn - max_turn_rad)
        relaxed_candidate_score = (
            -abs(length_m - target_length_m)
            - heading_penalty_weight * heading_delta
            - relaxed_turn_penalty
            - relaxed_largest_turn_penalty
            + geodesic_bonus
        )
        if relaxed_candidate_score > relaxed_score:
            relaxed_score = relaxed_candidate_score
            relaxed_path = path_world
            relaxed_goal = {
                "goal_x": float(path_world[-1, 0]),
                "goal_y": float(path_world[-1, 1]),
                "path_length_m": float(length_m),
                "geodesic_length_m": float(geodesic_length_m),
                "turn_count": float(turn_count),
                "largest_turn_deg": float(math.degrees(largest_turn)),
                "heading_delta_deg": float(math.degrees(heading_delta)),
                "selection_mode": "relaxed",
            }
        if length_m < min_length or length_m > max_length:
            continue
        if heading_delta > max_start_heading_deviation_rad:
            continue
        if turn_count < min_turn_count or turn_count > max_turn_count:
            continue
        if largest_turn > max_turn_rad:
            continue
        score = relaxed_candidate_score + 0.2 * turn_count
        if score > best_score:
            best_score = score
            best_path = path_world
            best_goal = {
                "goal_x": float(path_world[-1, 0]),
                "goal_y": float(path_world[-1, 1]),
                "path_length_m": float(length_m),
                "geodesic_length_m": float(geodesic_length_m),
                "turn_count": float(turn_count),
                "largest_turn_deg": float(math.degrees(largest_turn)),
                "heading_delta_deg": float(math.degrees(heading_delta)),
                "selection_mode": "strict",
            }

    if best_path is None or best_goal is None:
        if relaxed_path is None or relaxed_goal is None:
            if log_fn is not None:
                log_fn("planner: goal search found no acceptable single-goal path")
            return None
        if log_fn is not None:
            log_fn(
                "planner: goal search using relaxed winner "
                f"length={relaxed_goal['path_length_m']:.2f} geodesic={relaxed_goal['geodesic_length_m']:.2f} "
                f"turns={relaxed_goal['turn_count']:.0f} largest_turn_deg={relaxed_goal['largest_turn_deg']:.1f} "
                f"heading_delta_deg={relaxed_goal['heading_delta_deg']:.1f}"
            )
        return relaxed_path, relaxed_goal
    if log_fn is not None:
        log_fn(
            "planner: goal search winner "
            f"length={best_goal['path_length_m']:.2f} geodesic={best_goal['geodesic_length_m']:.2f} "
            f"turns={best_goal['turn_count']:.0f} largest_turn_deg={best_goal['largest_turn_deg']:.1f} "
            f"heading_delta_deg={best_goal['heading_delta_deg']:.1f}"
        )
    return best_path, best_goal


def choose_segment_path(
    *,
    occupancy_map: object,
    free_mask: np.ndarray,
    path_planner: object,
    start_px_xy: np.ndarray,
    segment_target_length_m: float,
    min_segment_length_m: float,
    max_segment_length_m: float,
    previous_heading_rad: float | None,
    min_turn_rad: float,
    max_turn_rad: float | None,
    desired_heading_rad: float | None,
    max_heading_deviation_rad: float | None,
    heading_penalty_weight: float,
    sample_candidates: int,
) -> tuple[np.ndarray, float, float | None]:
    start_tuple = (int(start_px_xy[1]), int(start_px_xy[0]))
    output = path_planner.generate_paths(start_tuple, free_mask)
    visited_indices = np.argwhere(output.visited != 0)
    if visited_indices.size == 0:
        raise RuntimeError("path planner found no reachable endpoints")

    rng = np.random.default_rng(visited_indices.shape[0] + int(start_px_xy[0]) + int(start_px_xy[1]))
    if len(visited_indices) > sample_candidates:
        sample_ids = rng.choice(len(visited_indices), size=sample_candidates, replace=False)
        visited_indices = visited_indices[sample_ids]

    best_score = -1e18
    best_world_path: np.ndarray | None = None
    best_length = 0.0
    best_heading: float | None = None

    for candidate_yx in visited_indices:
        path_yx = output.unroll_path((int(candidate_yx[0]), int(candidate_yx[1])))
        if len(path_yx) < 2:
            continue
        path_xy = path_yx[:, ::-1].astype(np.float64)
        path_world = occupancy_map.pixel_to_world_numpy(path_xy)
        path_world = shortcut_path(occupancy_map, free_mask, path_world)
        path_world = compress_path(path_world)
        length_m = segment_length(path_world)
        if length_m < min_segment_length_m or length_m > max_segment_length_m:
            continue
        initial_delta = path_world[1] - path_world[0]
        if np.linalg.norm(initial_delta) < 1e-6:
            continue
        heading = math.atan2(float(initial_delta[1]), float(initial_delta[0]))
        turn_bonus = 0.0
        heading_penalty = 0.0
        if desired_heading_rad is not None:
            heading_delta = abs(wrap_angle(heading - desired_heading_rad))
            if max_heading_deviation_rad is not None and heading_delta > max_heading_deviation_rad:
                continue
            heading_penalty = heading_delta
        if previous_heading_rad is not None:
            turn_delta = abs(wrap_angle(heading - previous_heading_rad))
            if turn_delta < min_turn_rad:
                continue
            if max_turn_rad is not None and turn_delta > max_turn_rad:
                continue
            turn_bonus = turn_delta
        score = -abs(length_m - segment_target_length_m) - heading_penalty_weight * heading_penalty + 0.25 * turn_bonus
        if score > best_score:
            best_score = score
            best_world_path = path_world
            best_length = length_m
            best_heading = heading

    if best_world_path is None:
        # Fall back to the furthest reachable point if turn constraints are too strict.
        furthest_index = np.unravel_index(int(np.argmax(output.distance_to_start)), output.distance_to_start.shape)
        path_yx = output.unroll_path((int(furthest_index[0]), int(furthest_index[1])))
        if len(path_yx) < 2:
            raise RuntimeError("path planner could not construct a usable fallback segment")
        path_xy = path_yx[:, ::-1].astype(np.float64)
        best_world_path = occupancy_map.pixel_to_world_numpy(path_xy)
        best_world_path = shortcut_path(occupancy_map, free_mask, best_world_path)
        best_world_path = compress_path(best_world_path)
        best_length = segment_length(best_world_path)
        if len(best_world_path) >= 2:
            delta = best_world_path[1] - best_world_path[0]
            best_heading = math.atan2(float(delta[1]), float(delta[0]))

    return best_world_path, best_length, best_heading


def build_long_route(
    *,
    occupancy_map: object,
    path_planner: object,
    start_world_xy: np.ndarray,
    target_length_m: float,
    segment_target_length_m: float,
    min_segment_length_m: float,
    max_segment_length_m: float,
    max_segments: int,
    start_heading_rad: float,
    max_start_heading_deviation_rad: float,
    start_heading_penalty_weight: float,
    min_turn_rad: float,
    max_turn_rad: float,
    sample_candidates: int,
) -> tuple[np.ndarray, list[dict[str, float]]]:
    free_mask = occupancy_map.buffered_meters(0.0).freespace_mask()
    start_px_xy = find_nearest_free_pixel(occupancy_map.world_to_pixel_numpy(start_world_xy[None, :])[0], free_mask)

    route_segments: list[np.ndarray] = []
    metadata: list[dict[str, float]] = []
    previous_heading: float | None = None
    accumulated_length_m = 0.0
    current_world_xy = occupancy_map.pixel_to_world_numpy(start_px_xy[None, :].astype(np.float64))[0]

    for segment_index in range(max_segments):
        segment_world, segment_length_m, segment_heading = choose_segment_path(
            occupancy_map=occupancy_map,
            free_mask=free_mask,
            path_planner=path_planner,
            start_px_xy=start_px_xy,
            segment_target_length_m=segment_target_length_m,
            min_segment_length_m=min_segment_length_m,
            max_segment_length_m=max_segment_length_m,
            previous_heading_rad=previous_heading,
            min_turn_rad=min_turn_rad,
            max_turn_rad=max_turn_rad,
            desired_heading_rad=start_heading_rad if previous_heading is None else None,
            max_heading_deviation_rad=max_start_heading_deviation_rad if previous_heading is None else None,
            heading_penalty_weight=start_heading_penalty_weight,
            sample_candidates=sample_candidates,
        )
        if route_segments:
            segment_world = segment_world[1:]
        route_segments.append(segment_world)
        accumulated_length_m += segment_length_m
        metadata.append(
            {
                "segment_index": float(segment_index),
                "length_m": float(segment_length_m),
                "start_x": float(current_world_xy[0]),
                "start_y": float(current_world_xy[1]),
                "end_x": float(segment_world[-1, 0]),
                "end_y": float(segment_world[-1, 1]),
            }
        )
        current_world_xy = segment_world[-1]
        start_px_xy = find_nearest_free_pixel(
            occupancy_map.world_to_pixel_numpy(current_world_xy[None, :])[0],
            free_mask,
        )
        previous_heading = segment_heading
        if accumulated_length_m >= target_length_m and len(route_segments) >= 2:
            break

    world_path = np.concatenate(route_segments, axis=0)
    return world_path, metadata


def main() -> int:
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    output_json = Path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    trace_path = output_json.with_suffix(".trace.log")

    def log(message: str) -> None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        with trace_path.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")
        print(message, flush=True)

    isaac_sim_root = Path(os.environ.get("ISAAC_SIM_ROOT", "/home/peng/IsaacSim"))
    ext_root = isaac_sim_root / "_build/linux-x86_64/release/exts"
    extra_sys_paths = [
        ext_root / "isaacsim.asset.gen.omap",
        ext_root / "isaacsim.replicator.mobility_gen",
    ]
    for extra_path in extra_sys_paths:
        extra_path_str = str(extra_path)
        if extra_path.exists() and extra_path_str not in sys.path:
            sys.path.append(extra_path_str)
        package_root = extra_path / "isaacsim"
        if package_root.exists() and str(package_root) not in isaacsim.__path__:
            isaacsim.__path__.append(str(package_root))

    app = SimulationApp({"headless": args.headless, "disable_viewport_updates": args.headless})
    try:
        import omni.kit.app
        import omni.physx
        import omni.usd
        from isaacsim.asset.gen.omap.bindings import _omap
        from isaacsim.core.api import SimulationContext
        from isaacsim.core.utils.stage import add_reference_to_stage, is_stage_loading, open_stage
        from isaacsim.core.utils.xforms import get_world_pose
        from isaacsim.replicator.mobility_gen.impl.occupancy_map import OccupancyMap
        from isaacsim.replicator.mobility_gen.impl.path_planner import generate_paths
        from pxr import Sdf, UsdGeom, UsdPhysics

        log("planner: imports complete")

        scene_path = str(Path(args.scene).resolve())
        robot_path = str(Path(args.robot).resolve())
        open_stage(scene_path)
        app.update()
        app.update()
        while is_stage_loading():
            app.update()
        log("planner: scene loaded")

        add_reference_to_stage(robot_path, args.robot_prim_path)
        for _ in range(max(1, int(args.warmup_frames))):
            app.update()
        log("planner: robot referenced and warmup finished")

        stage = omni.usd.get_context().get_stage()
        if not stage.GetPrimAtPath("/World/physicsScene").IsValid():
            UsdPhysics.Scene.Define(stage, Sdf.Path("/World/physicsScene"))
            app.update()
        log("planner: physics scene ready")

        simulation_context = SimulationContext(stage_units_in_meters=1.0)
        simulation_context.play()
        for _ in range(10):
            simulation_context.step(render=False)
        log("planner: simulation stepped before occupancy generation")

        position, orientation = get_world_pose(args.robot_base_prim_path)
        start_world_z = float(position[2])
        start_world = Pose2D(
            x=float(position[0]),
            y=float(position[1]),
            yaw_rad=float(2.0 * math.atan2(float(orientation[2]), float(orientation[3]))),
        )
        log(
            "planner: start pose world="
            f"({start_world.x:.3f}, {start_world.y:.3f}, {start_world_z:.3f}, {start_world.yaw_rad:.3f})"
        )

        bbox_cache = UsdGeom.BBoxCache(0.0, [UsdGeom.Tokens.default_], useExtentsHint=True)
        world_prim = stage.GetPrimAtPath("/World")
        bbox = bbox_cache.ComputeWorldBound(world_prim)
        aligned = bbox.ComputeAlignedRange()
        min_bound = aligned.GetMin()
        max_bound = aligned.GetMax()
        bbox_min_xy = np.array([float(min_bound[0]) - args.bounds_margin_m, float(min_bound[1]) - args.bounds_margin_m])
        bbox_max_xy = np.array([float(max_bound[0]) + args.bounds_margin_m, float(max_bound[1]) + args.bounds_margin_m])
        fallback_min_xy = np.array([start_world.x - args.map_half_extent_m, start_world.y - args.map_half_extent_m])
        fallback_max_xy = np.array([start_world.x + args.map_half_extent_m, start_world.y + args.map_half_extent_m])
        min_xy = np.minimum(bbox_min_xy, fallback_min_xy)
        max_xy = np.maximum(bbox_max_xy, fallback_max_xy)
        log(
            "planner: bbox min="
            f"{bbox_min_xy.tolist()} max={bbox_max_xy.tolist()} -> using map bounds "
            f"{min_xy.tolist()} to {max_xy.tolist()}"
        )

        physx = omni.physx.get_physx_interface()
        occupancy_source = "physx_omap"
        visual_mesh_summary: dict[str, int] | None = None
        generator = _omap.Generator(physx, omni.usd.get_context().get_stage_id())
        generator.update_settings(float(args.cell_size_m), 4, 5, 6)
        generator.set_transform(
            (0.0, 0.0, start_world_z + float(args.omap_origin_z_offset_m)),
            (float(min_xy[0]), float(min_xy[1]), float(args.omap_z_min_m)),
            (float(max_xy[0]), float(max_xy[1]), float(args.omap_z_max_m)),
        )
        generator.generate2d()
        dims = generator.get_dimensions()
        log(f"planner: occupancy generated dims={dims}")
        width_px = int(dims[0])
        height_px = int(dims[1])
        raw = np.array(generator.get_buffer(), dtype=np.uint8).reshape((height_px, width_px))
        raw_values, raw_counts = np.unique(raw, return_counts=True)
        log(
            "planner: raw occupancy values="
            + ", ".join(f"{int(value)}:{int(count)}" for value, count in zip(raw_values.tolist(), raw_counts.tolist()))
        )
        freespace_mask = raw == 5
        occupied_mask = raw == 4
        if int(np.count_nonzero(occupied_mask)) == 0:
            z_window_world = (
                start_world_z + float(args.omap_origin_z_offset_m) + float(args.omap_z_min_m),
                start_world_z + float(args.omap_origin_z_offset_m) + float(args.omap_z_max_m),
            )
            occupied_mask, visual_mesh_summary = build_visual_mesh_bbox_occupancy(
                stage=stage,
                bbox_cache=bbox_cache,
                min_xy=min_xy,
                max_xy=max_xy,
                resolution_m=float(args.cell_size_m),
                z_window_world=z_window_world,
            )
            freespace_mask = ~occupied_mask
            occupancy_source = "visual_mesh_bbox_fallback"
            log(
                "planner: raw occupancy empty, using visual mesh bbox fallback "
                + ", ".join(f"{key}={value}" for key, value in visual_mesh_summary.items())
            )
        occupancy_map = OccupancyMap.from_masks(
            freespace_mask=freespace_mask,
            occupied_mask=occupied_mask,
            resolution=float(args.cell_size_m),
            origin=(float(min_xy[0]), float(min_xy[1]), 0.0),
        ).buffered_meters(float(args.clearance_m))
        log("planner: occupancy masks ready")

        start_world_xy = np.array([start_world.x, start_world.y], dtype=np.float64)
        planner_adapter = type("PathPlannerAdapter", (), {"generate_paths": staticmethod(generate_paths)})
        route_mode = "single_goal"
        single_goal_result = choose_goal_path(
            occupancy_map=occupancy_map,
            path_planner=planner_adapter,
            start_world_xy=start_world_xy,
            target_length_m=float(args.target_length_m),
            path_length_tolerance_m=float(args.path_length_tolerance_m),
            desired_start_heading_rad=float(args.start_heading_rad),
            max_start_heading_deviation_rad=math.radians(float(args.max_start_heading_deg)),
            min_turn_rad=math.radians(float(args.min_turn_deg)),
            max_turn_rad=math.radians(float(args.max_turn_deg)),
            min_turn_count=int(args.min_turn_count),
            max_turn_count=int(args.max_turn_count),
            heading_penalty_weight=float(args.start_heading_penalty_weight),
            sample_candidates=int(args.sample_candidates),
            max_goal_path_evals=int(args.max_goal_path_evals),
            distance_resolution_m=float(args.cell_size_m),
            log_fn=log,
        )
        if single_goal_result is not None:
            world_path, goal_summary = single_goal_result
            segment_metadata = [goal_summary]
        else:
            route_mode = "multi_segment_fallback"
            world_path, segment_metadata = build_long_route(
                occupancy_map=occupancy_map,
                path_planner=planner_adapter,
                start_world_xy=start_world_xy,
                target_length_m=float(args.target_length_m),
                segment_target_length_m=float(args.segment_target_length_m),
                min_segment_length_m=float(args.min_segment_length_m),
                max_segment_length_m=float(args.max_segment_length_m),
                max_segments=int(args.max_segments),
                start_heading_rad=float(args.start_heading_rad),
                max_start_heading_deviation_rad=math.radians(float(args.max_start_heading_deg)),
                start_heading_penalty_weight=float(args.start_heading_penalty_weight),
                min_turn_rad=math.radians(float(args.min_turn_deg)),
                max_turn_rad=math.radians(float(args.max_turn_deg)),
                sample_candidates=int(args.sample_candidates),
            )
        log(f"planner: route built with {len(world_path)} waypoints in mode={route_mode}")
        local_path = np.stack([subtract_start_translation(point, start_world) for point in world_path], axis=0)
        local_path = np.concatenate([local_path, np.zeros((local_path.shape[0], 1), dtype=np.float64)], axis=1)

        payload = {
            "scene_path": scene_path,
            "robot_path": robot_path,
            "robot_prim_path": args.robot_prim_path,
            "robot_base_prim_path": args.robot_base_prim_path,
            "cell_size_m": float(args.cell_size_m),
            "clearance_m": float(args.clearance_m),
            "target_length_m": float(args.target_length_m),
            "planned_length_m": segment_length(world_path),
            "planned_turn_count": count_turns(local_path[:, :2], math.radians(float(args.min_turn_deg))),
            "route_mode": route_mode,
            "start_heading_rad": float(args.start_heading_rad),
            "max_start_heading_deg": float(args.max_start_heading_deg),
            "max_turn_deg": float(args.max_turn_deg),
            "path_length_tolerance_m": float(args.path_length_tolerance_m),
            "min_turn_count": int(args.min_turn_count),
            "max_turn_count": int(args.max_turn_count),
            "start_world_pose": asdict(start_world),
            "occupancy_origin_world": {"x": float(min_xy[0]), "y": float(min_xy[1])},
            "occupancy_dimensions_px": {"width": width_px, "height": height_px},
            "occupancy_source": occupancy_source,
            "occupancy_z_window_m": {
                "origin_z": float(start_world_z + float(args.omap_origin_z_offset_m)),
                "min_z": float(args.omap_z_min_m),
                "max_z": float(args.omap_z_max_m),
            },
            "segment_summaries": segment_metadata,
            "waypoints_world": [
                {"x": float(point[0]), "y": float(point[1]), "yaw_rad": 0.0} for point in world_path
            ],
            "waypoints_local_start_frame": [
                {"x": float(point[0]), "y": float(point[1]), "yaw_rad": 0.0} for point in local_path[:, :2]
            ],
        }

        if args.output_map_dir:
            output_map_dir = Path(args.output_map_dir)
            output_map_dir.mkdir(parents=True, exist_ok=True)
            occupancy_map.save_ros(str(output_map_dir))
            payload["occupancy_ros_map_dir"] = str(output_map_dir)
            debug_png = output_map_dir / "debug_topdown.png"
            debug_summary_json = output_map_dir / "debug_topdown_summary.json"
            save_debug_plan_topdown(
                raw_buffer=raw,
                origin_xy=min_xy,
                resolution_m=float(args.cell_size_m),
                world_path=world_path,
                output_png=debug_png,
                output_json=debug_summary_json,
            )
            payload["debug_topdown_png"] = str(debug_png)
            payload["debug_topdown_summary_json"] = str(debug_summary_json)
            log(f"planner: occupancy map exported to {output_map_dir}")
        if visual_mesh_summary is not None:
            payload["visual_mesh_fallback_summary"] = visual_mesh_summary

        output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log(f"planner: payload written to {output_json}")
        print(json.dumps(payload, indent=2), flush=True)
        simulation_context.stop()
        return 0
    except Exception:
        error_text = traceback.format_exc()
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        trace_path.write_text(trace_path.read_text(encoding="utf-8") + error_text if trace_path.exists() else error_text, encoding="utf-8")
        print(error_text, flush=True)
        raise
    finally:
        app.close()


if __name__ == "__main__":
    raise SystemExit(main())
