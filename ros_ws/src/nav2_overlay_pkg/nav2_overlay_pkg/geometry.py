from __future__ import annotations

import json
import math
from pathlib import Path

from semantic_mapper_pkg.models import CameraIntrinsics, Pose2D, SemanticDetection


class GeometricMapBuilder:
    """Build a small 2D occupancy-style grid from localized semantic depth observations."""

    def __init__(self, resolution_m: float = 0.25) -> None:
        self.resolution_m = resolution_m
        self._scores: dict[tuple[int, int], int] = {}
        self.path: list[dict[str, float]] = []
        self.observed_points: list[dict[str, object]] = []

    def add_observation(
        self,
        *,
        frame_id: str,
        pose: Pose2D,
        intrinsics: CameraIntrinsics,
        detections: list[SemanticDetection],
    ) -> None:
        self.path.append(
            {
                "frame_id": frame_id,
                "x": round(pose.x, 4),
                "y": round(pose.y, 4),
                "yaw": round(pose.yaw, 4),
            }
        )
        start_cell = self._world_to_cell(pose.x, pose.y)
        for detection in detections:
            world_x, world_y = self._project_detection(pose, intrinsics, detection)
            end_cell = self._world_to_cell(world_x, world_y)
            ray_cells = self._raytrace_cells(start_cell, end_cell)
            for cell in ray_cells[:-1]:
                self._scores[cell] = max(self._scores.get(cell, 0) - 1, -8)
            self._scores[end_cell] = min(self._scores.get(end_cell, 0) + 4, 12)
            self.observed_points.append(
                {
                    "frame_id": frame_id,
                    "label": detection.label,
                    "x": round(world_x, 4),
                    "y": round(world_y, 4),
                    "depth_m": round(detection.depth_m, 4),
                }
            )

    def export(self) -> dict[str, object]:
        cells = set(self._scores.keys())
        for step in self.path:
            cells.add(self._world_to_cell(step["x"], step["y"]))

        if not cells:
            min_x = min_y = max_x = max_y = 0
        else:
            min_x = min(cell[0] for cell in cells)
            max_x = max(cell[0] for cell in cells)
            min_y = min(cell[1] for cell in cells)
            max_y = max(cell[1] for cell in cells)

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        grid: list[list[int]] = []
        occupied_cells: list[dict[str, object]] = []
        free_cells: list[dict[str, object]] = []
        for iy in range(min_y, max_y + 1):
            row: list[int] = []
            for ix in range(min_x, max_x + 1):
                score = self._scores.get((ix, iy), 0)
                if score >= 2:
                    value = 100
                    occupied_cells.append(self._cell_payload(ix, iy, score))
                elif score <= -1:
                    value = 0
                    free_cells.append(self._cell_payload(ix, iy, score))
                else:
                    value = -1
                row.append(value)
            grid.append(row)

        return {
            "resolution_m": self.resolution_m,
            "origin": {
                "x": round(min_x * self.resolution_m, 4),
                "y": round(min_y * self.resolution_m, 4),
            },
            "width": width,
            "height": height,
            "occupied_count": len(occupied_cells),
            "free_count": len(free_cells),
            "path": self.path,
            "observed_points": self.observed_points,
            "occupied_cells": occupied_cells,
            "free_cells": free_cells,
            "grid": grid,
        }

    def export_to_path(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.export(), indent=2), encoding="utf-8")
        return path

    def _project_detection(
        self,
        pose: Pose2D,
        intrinsics: CameraIntrinsics,
        detection: SemanticDetection,
    ) -> tuple[float, float]:
        lateral = ((detection.pixel_x - intrinsics.cx) / intrinsics.fx) * detection.depth_m
        cos_yaw = math.cos(pose.yaw)
        sin_yaw = math.sin(pose.yaw)
        world_x = pose.x + (cos_yaw * detection.depth_m) - (sin_yaw * lateral)
        world_y = pose.y + (sin_yaw * detection.depth_m) + (cos_yaw * lateral)
        return (world_x, world_y)

    def _world_to_cell(self, x: float, y: float) -> tuple[int, int]:
        return (
            int(round(x / self.resolution_m)),
            int(round(y / self.resolution_m)),
        )

    def _cell_payload(self, ix: int, iy: int, score: int) -> dict[str, object]:
        return {
            "cell": {"x": ix, "y": iy},
            "world": {
                "x": round(ix * self.resolution_m, 4),
                "y": round(iy * self.resolution_m, 4),
            },
            "score": score,
        }

    def _raytrace_cells(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> list[tuple[int, int]]:
        x0, y0 = start
        x1, y1 = end
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        cells: list[tuple[int, int]] = []
        while True:
            cells.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return cells
