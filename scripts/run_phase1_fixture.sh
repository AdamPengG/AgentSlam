#!/usr/bin/env bash
# Run the offline semantic mapping baseline on the synthetic GT-pose fixture and write artifacts to artifacts/phase1.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="${ROOT_DIR}/ros_ws/src/semantic_mapper_pkg${PYTHONPATH:+:${PYTHONPATH}}" \
/usr/bin/python3 -m semantic_mapper_pkg.ros_node \
  --mode fixture \
  --fixture "${ROOT_DIR}/fixtures/semantic_mapping/synthetic_gt_pose_scene.json" \
  --output "${ROOT_DIR}/artifacts/phase1/synthetic_semantic_map.json" \
  --query-output-dir "${ROOT_DIR}/artifacts/phase1" \
  --query-label chair \
  --query-label table \
  --merge-distance 0.8
