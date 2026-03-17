from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .map_builder import SemanticMapBuilder
from .models import FrameObservation, Pose2D, SemanticDetection


@dataclass(frozen=True)
class DetectionEnvelope:
    frame_id: str
    detections: list[SemanticDetection]
    source_mode: str = "unknown"


def build_frame_observation(
    *,
    frame_id: str,
    pose: Pose2D,
    intrinsics,
    detections: list[SemanticDetection],
) -> FrameObservation:
    return FrameObservation(
        frame_id=frame_id,
        pose=pose,
        intrinsics=intrinsics,
        detections=detections,
    )


def parse_detection_envelope(payload: str) -> DetectionEnvelope:
    data = json.loads(payload)
    return DetectionEnvelope(
        frame_id=data["frame_id"],
        source_mode=data.get("source_mode", "unknown"),
        detections=[
            SemanticDetection(
                label=item["label"],
                pixel_x=item["pixel_x"],
                pixel_y=item["pixel_y"],
                depth_m=item["depth_m"],
                confidence=item.get("confidence", 1.0),
            )
            for item in data.get("detections", [])
        ],
    )


def load_exported_map(path: str | Path) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def query_exported_map(
    payload: dict[str, object],
    label_query: str,
    *,
    near_x: float | None = None,
    near_y: float | None = None,
    radius_m: float | None = None,
    min_observations: int = 1,
    limit: int = 0,
) -> dict[str, object]:
    reference_point = _validate_query_filters(
        near_x=near_x,
        near_y=near_y,
        radius_m=radius_m,
        min_observations=min_observations,
        limit=limit,
    )
    matches: list[dict[str, object]] = []
    for item in payload.get("objects", []):
        label = str(item.get("label", ""))
        if label_query.lower() not in label.lower():
            continue
        observation_count = int(item.get("observation_count", 0) or 0)
        if observation_count < min_observations:
            continue

        match = dict(item)
        if reference_point is not None:
            position = item.get("position", {})
            distance_m = math.dist(
                (
                    float(position.get("x", 0.0)),
                    float(position.get("y", 0.0)),
                ),
                reference_point,
            )
            if radius_m is not None and distance_m > radius_m:
                continue
            match["distance_m"] = round(distance_m, 4)
        matches.append(match)

    matches.sort(
        key=lambda item: (
            float(item.get("distance_m", 1.0e12)),
            -float(item.get("observation_count", 0)),
            str(item.get("object_id", "")),
        )
    )
    returned_matches = matches[:limit] if limit > 0 else matches
    return {
        "query": label_query,
        "filters": _query_filters_payload(
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


def export_query_results(
    builder: SemanticMapBuilder,
    query_labels: Iterable[str],
    output_dir: str | Path,
) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for label in query_labels:
        query_payload = builder.query(label)
        output_path = output_dir / f"query_{slugify_label(label)}.json"
        output_path.write_text(json.dumps(query_payload, indent=2), encoding="utf-8")
        paths.append(output_path)
    return paths


def export_query_results_from_map(
    payload: dict[str, object],
    query_labels: Iterable[str],
    output_dir: str | Path,
) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for label in query_labels:
        query_payload = query_exported_map(payload, label)
        output_path = output_dir / f"query_{slugify_label(label)}.json"
        output_path.write_text(json.dumps(query_payload, indent=2), encoding="utf-8")
        paths.append(output_path)
    return paths


def slugify_label(label: str) -> str:
    compact = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return compact or "query"


def _validate_query_filters(
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
