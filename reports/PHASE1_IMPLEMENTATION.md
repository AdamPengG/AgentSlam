# Phase 1 Implementation

## Deliverables

- ROS package skeletons created under `ros_ws/src/`
- `semantic_mapper_pkg` implemented with:
  - GT-pose-aware projection
  - simple object fusion by label and merge distance
  - JSON export
  - label-query path
- synthetic fixture added at `fixtures/semantic_mapping/synthetic_gt_pose_scene.json`
- runnable offline demo script added at `scripts/run_phase1_fixture.sh`
- example outputs written under `artifacts/phase1/`

## Representation Choice

- object centroid list plus label statistics
- rationale:
  - easy to validate
  - easy to export
  - easy to query
  - low maintenance cost for the first working baseline

## Package Layout Added

- `sim_bridge_pkg`
- `semantic_mapper_pkg`
- `room_graph_pkg`
- `semantic_query_pkg`
- `nav2_overlay_pkg`
- `localization_adapter_pkg`
- `eval_tools_pkg`

## Deferred Work

- room graph enrichment
- online simulator-fed fusion path
- richer query APIs
- Nav2 runtime integration
