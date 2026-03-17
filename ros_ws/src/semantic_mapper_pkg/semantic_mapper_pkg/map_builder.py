from __future__ import annotations

import json
import math
from pathlib import Path

from .models import FrameObservation, SemanticObject


class SemanticMapBuilder:
    """Fuses GT-pose-aligned semantic detections into a small object map."""

    def __init__(self, merge_distance_m: float = 0.75) -> None:
        self.merge_distance_m = merge_distance_m
        self.objects: list[SemanticObject] = []
        self._label_counters: dict[str, int] = {}

    def add_frame(self, frame: FrameObservation) -> None:
        for detection in frame.detections:
            world_x, world_y, world_z = self._project_detection(frame, detection)
            self._merge_or_create(
                label=detection.label,
                x=world_x,
                y=world_y,
                z=world_z,
                confidence=detection.confidence,
                frame_id=frame.frame_id,
            )

    def query(
        self,
        label_query: str,
        *,
        near_x: float | None = None,
        near_y: float | None = None,
        radius_m: float | None = None,
        min_observations: int = 1,
        limit: int = 0,
    ) -> dict[str, object]:
        reference_point = self._validate_query_filters(
            near_x=near_x,
            near_y=near_y,
            radius_m=radius_m,
            min_observations=min_observations,
            limit=limit,
        )
        matches: list[dict[str, object]] = []
        for obj in self.objects:
            if label_query.lower() not in obj.label.lower():
                continue
            if obj.observation_count < min_observations:
                continue

            match = self._object_to_payload(obj)
            if reference_point is not None:
                distance_m = math.dist((obj.x, obj.y), reference_point)
                if radius_m is not None and distance_m > radius_m:
                    continue
                match["distance_m"] = round(distance_m, 4)
            matches.append(match)

        matches.sort(key=self._query_sort_key)
        returned_matches = matches[:limit] if limit > 0 else matches
        return {
            "query": label_query,
            "filters": self._query_filters_payload(
                near_x=near_x,
                near_y=near_y,
                radius_m=radius_m,
                min_observations=min_observations,
                limit=limit,
            ),
            "match_count": len(matches),
            "returned_match_count": len(returned_matches),
            "matches": returned_matches,
        }

    def export(self) -> dict[str, object]:
        labels: dict[str, int] = {}
        for obj in self.objects:
            labels[obj.label] = labels.get(obj.label, 0) + 1
        return {
            "object_count": len(self.objects),
            "labels": labels,
            "objects": [self._object_to_payload(obj) for obj in self.objects],
            "config": {"merge_distance_m": self.merge_distance_m},
        }

    def export_to_path(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.export(), indent=2), encoding="utf-8")
        return path

    def _project_detection(self, frame: FrameObservation, detection) -> tuple[float, float, float]:
        # Approximate a forward-facing pinhole camera. Depth projects forward,
        # horizontal pixel offset projects laterally, and vertical offset maps to height.
        intrinsics = frame.intrinsics
        lateral = ((detection.pixel_x - intrinsics.cx) / intrinsics.fx) * detection.depth_m
        vertical = ((detection.pixel_y - intrinsics.cy) / intrinsics.fy) * detection.depth_m

        cos_yaw = math.cos(frame.pose.yaw)
        sin_yaw = math.sin(frame.pose.yaw)

        world_x = frame.pose.x + (cos_yaw * detection.depth_m) - (sin_yaw * lateral)
        world_y = frame.pose.y + (sin_yaw * detection.depth_m) + (cos_yaw * lateral)
        world_z = frame.pose.z - vertical
        return world_x, world_y, world_z

    def _merge_or_create(
        self,
        *,
        label: str,
        x: float,
        y: float,
        z: float,
        confidence: float,
        frame_id: str,
    ) -> None:
        candidate = self._find_candidate(label=label, x=x, y=y)
        if candidate is not None:
            candidate.update(x=x, y=y, z=z, confidence=confidence, frame_id=frame_id)
            return

        counter = self._label_counters.get(label, 0) + 1
        self._label_counters[label] = counter
        self.objects.append(
            SemanticObject(
                object_id=f"{label}-{counter}",
                label=label,
                x=x,
                y=y,
                z=z,
                observation_count=1,
                confidence_sum=confidence,
                frames=[frame_id],
            )
        )

    def _find_candidate(self, *, label: str, x: float, y: float) -> SemanticObject | None:
        for obj in self.objects:
            if obj.label != label:
                continue
            if math.dist((obj.x, obj.y), (x, y)) <= self.merge_distance_m:
                return obj
        return None

    def _object_to_payload(self, obj: SemanticObject) -> dict[str, object]:
        return {
            "object_id": obj.object_id,
            "label": obj.label,
            "position": {"x": round(obj.x, 4), "y": round(obj.y, 4), "z": round(obj.z, 4)},
            "observation_count": obj.observation_count,
            "mean_confidence": round(obj.mean_confidence, 4),
            "frames": obj.frames,
        }

    def _validate_query_filters(
        self,
        *,
        near_x: float | None,
        near_y: float | None,
        radius_m: float | None,
        min_observations: int,
        limit: int,
    ) -> tuple[float, float] | None:
        if (near_x is None) != (near_y is None):
            raise ValueError("near_x and near_y must be provided together")
        if radius_m is not None and radius_m < 0.0:
            raise ValueError("radius_m must be >= 0")
        if min_observations < 1:
            raise ValueError("min_observations must be >= 1")
        if limit < 0:
            raise ValueError("limit must be >= 0")
        if near_x is None or near_y is None:
            return None
        return (near_x, near_y)

    def _query_filters_payload(
        self,
        *,
        near_x: float | None,
        near_y: float | None,
        radius_m: float | None,
        min_observations: int,
        limit: int,
    ) -> dict[str, object]:
        payload: dict[str, object] = {"min_observations": min_observations}
        if near_x is not None and near_y is not None:
            payload["reference_point"] = {"x": round(near_x, 4), "y": round(near_y, 4)}
        if radius_m is not None:
            payload["radius_m"] = round(radius_m, 4)
        if limit > 0:
            payload["limit"] = limit
        return payload

    def _query_sort_key(self, item: dict[str, object]) -> tuple[float, float, str]:
        distance_m = float(item.get("distance_m", 1.0e12))
        observation_score = -float(item.get("observation_count", 0))
        object_id = str(item.get("object_id", ""))
        return (distance_m, observation_score, object_id)
