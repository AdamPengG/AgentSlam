# Phase 1 Semantic Mapping

## Goal

Deliver a semantic mapping baseline that keeps the offline regression path while adding a real ROS topic consumer that can be driven by replay now and live Isaac later.

## Chosen Representation

Current choice: object centroid list plus label statistics.

Why this is the right Phase 1 tradeoff:

- easy to validate with synthetic GT-pose fixtures
- easy to export as JSON
- easy to query by label
- easy to feed from replay without inventing a custom semantic graph too early

## Supported Modes

- `fixture`
  - runs directly from JSON fixtures
- `bag_replay`
  - consumes ROS topics, typically through `ros2 bag play`
- `live_isaac`
  - reserved for the future live bridge path, using the same mapper node

## Current Inputs

- normalized localization odometry via `nav_msgs/msg/Odometry`
- GT pose remains the current raw fallback localization source through `localization_adapter_pkg`
- camera intrinsics via `sensor_msgs/msg/CameraInfo`
- semantic detections via JSON carried in `std_msgs/msg/String`
- RGB plus IMU as part of the Phase 1 topic contract
- depth is accepted when present

## Current Outputs

- semantic map JSON under `artifacts/phase1/`
- query result JSON files, including label-only and spatially filtered lookups
- runtime summary JSON for replay and fixture runs
- exploration progress JSON for offline viewpoint-order experiments

## Query Capabilities

- label substring matching
- optional `near_x` and `near_y` reference point
- optional `radius_m` radial filtering
- optional `min_observations` threshold
- optional `limit` for bounded result sets

This keeps Phase 1 on artifact-backed querying while still allowing simple "find a chair near this point"
style workflows.

## Exploration-Backed Map Growth

Phase 1 now includes a conservative offline exploration scaffold in `nav2_overlay_pkg`.

- input: a fixture containing candidate viewpoints with GT pose and semantic detections
- planner policy: greedy semantic-gain ordering with a small travel-distance penalty
- map update path: each visited frame is fused through the same `SemanticMapBuilder`
- outputs:
  - final semantic map JSON
  - per-step exploration progress JSON
  - exported query artifacts for selected labels

This is intentionally not a live Nav2 frontier explorer yet. It exists to validate the missing middle
piece between "pose + detections" and "map coverage grows because the robot visited more places."

## Localization-Backed Mapping Slice

Phase 1 now also includes a more realistic online slice that keeps localization, geometric mapping, and
semantic mapping on one normalized odometry topic.

- `localization_adapter_pkg` republishes `/agentslam/localization/odom`
- `nav2_overlay_pkg.localized_mapping` exports a lightweight 2D occupancy-style map
- `semantic_mapper_pkg.ros_node` now runs against the same normalized localization stream

This still uses GT as the current fallback odometry source, but it establishes the exact contract surface
that a future VSLAM backend can plug into without rewriting the semantic or geometric mapping layers.

## Minimal Demo

```bash
cd /home/peng/AgentSlam
bash scripts/run_phase1_fixture.sh
bash scripts/run_phase1_localized_mapping_demo.sh
bash scripts/run_phase1_exploration_demo.sh
bash scripts/run_phase1_replay_demo.sh
bash scripts/run_phase1_office_demo.sh
```

## Next Step

- replace the offline exploration ordering with a real Nav2-compatible exploration driver
- replace the GT-backed localization fallback with a real visual-SLAM backend
- replace the replay publisher with a real live Isaac ROS publisher
- decide whether TF and `/clock` should become strict runtime dependencies for Phase 2
