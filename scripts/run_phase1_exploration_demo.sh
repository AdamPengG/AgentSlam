#!/usr/bin/env bash
# Run an offline exploration scaffold that visits semantic viewpoints and grows a semantic map.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="${ROOT_DIR}/ros_ws/src/semantic_mapper_pkg:${ROOT_DIR}/ros_ws/src/nav2_overlay_pkg${PYTHONPATH:+:${PYTHONPATH}}" \
/usr/bin/python3 -m nav2_overlay_pkg.exploration_demo \
  --fixture "${ROOT_DIR}/fixtures/semantic_mapping/exploration_gt_pose_scene.json" \
  --output-map "${ROOT_DIR}/artifacts/phase1/exploration_semantic_map.json" \
  --output-progress "${ROOT_DIR}/artifacts/phase1/exploration_progress.json" \
  --query-output-dir "${ROOT_DIR}/artifacts/phase1/exploration_queries" \
  --query-label chair \
  --query-label cabinet \
  --query-label sofa \
  --merge-distance 0.8
