# Phase 1 Localized Mapping Validation

## Scope

Validate a more realistic Phase 1 runtime slice where localization, geometric mapping, and semantic mapping
share one normalized odometry topic.

## Commands Run

### Build

```bash
set +u
source /opt/ros/humble/setup.bash
set -u
cd /home/peng/AgentSlam/ros_ws
colcon build --packages-select sim_bridge_pkg semantic_mapper_pkg localization_adapter_pkg nav2_overlay_pkg
```

### Focused Unit Tests

```bash
PYTHONPATH=/home/peng/AgentSlam/ros_ws/src/semantic_mapper_pkg:/home/peng/AgentSlam/ros_ws/src/sim_bridge_pkg:/home/peng/AgentSlam/ros_ws/src/localization_adapter_pkg:/home/peng/AgentSlam/ros_ws/src/nav2_overlay_pkg \
/usr/bin/python3 -m unittest \
  ros_ws.src.localization_adapter_pkg.test.test_localization_core \
  ros_ws.src.nav2_overlay_pkg.test.test_geometry \
  ros_ws.src.semantic_mapper_pkg.test.test_semantic_mapper \
  ros_ws.src.semantic_mapper_pkg.test.test_runtime_contract
```

### End-to-End Localized Mapping Demo

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_localized_mapping_demo.sh
```

## Results

- package build: PASS
- focused unit tests: PASS
- localized mapping demo: PASS

## Key Outcomes

- `localization_adapter_pkg` successfully normalized odometry onto `/agentslam/localization/odom`
- the runtime stayed on GT fallback because the preferred VSLAM topic was absent, which is the expected current behavior
- `nav2_overlay_pkg.localized_mapping` exported a 2D occupancy-style grid with 6 occupied cells and 26 free cells
- `semantic_mapper_pkg.ros_node` consumed the normalized localization topic and fused all 3 replay frames
- early detection buffering prevented the first replay frame from being dropped

## Evidence

- localization runtime:
  - `artifacts/phase1/office_nova_localization_runtime.json`
- geometric map:
  - `artifacts/phase1/office_nova_localized_occupancy.json`
- geometric runtime:
  - `artifacts/phase1/office_nova_localized_occupancy_runtime.json`
- semantic map:
  - `artifacts/phase1/office_nova_localized_semantic_map.json`
- semantic runtime:
  - `artifacts/phase1/office_nova_localized_semantic_map_runtime.json`
- semantic queries:
  - `artifacts/phase1/localized_queries/query_chair.json`
  - `artifacts/phase1/localized_queries/query_desk.json`
  - `artifacts/phase1/localized_queries/query_cabinet.json`
- logs:
  - `artifacts/phase1/logs/localized_adapter.log`
  - `artifacts/phase1/logs/localized_geometry_mapper.log`
  - `artifacts/phase1/logs/localized_semantic_mapper.log`
  - `artifacts/phase1/logs/localized_replay_publisher.log`

## Current Limits

- the preferred `isaac_ros_visual_slam` backend is not yet installed in the current ROS environment
- the geometric map is a lightweight occupancy-style export from localized detection rays, not a full dense mapping backend
- the accepted runtime is still replay-backed rather than a live Isaac ROS topic bridge
