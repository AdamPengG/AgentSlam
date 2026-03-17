# Phase 1 Runtime Facts

## Execution Date

- date: `2026-03-16`
- timezone: `Asia/Shanghai`

## Commands Actually Run

### Focused Unit Tests

```bash
PYTHONPATH=/home/peng/AgentSlam/ros_ws/src/semantic_mapper_pkg:/home/peng/AgentSlam/ros_ws/src/sim_bridge_pkg \
/usr/bin/python3 -m unittest \
  ros_ws.src.semantic_mapper_pkg.test.test_semantic_mapper \
  ros_ws.src.semantic_mapper_pkg.test.test_runtime_contract \
  ros_ws.src.sim_bridge_pkg.test.test_fixture_io
```

Observed result:

- `Ran 6 tests`
- `OK`

### Offline Fixture Baseline

```bash
bash scripts/run_phase1_fixture.sh
```

Observed result:

- exported map contains `2` objects
- query outputs were written for `chair` and `table`

### Isaac Office + Nova Validation

```bash
bash scripts/run_isaac_office_nova.sh --validate-only
```

Observed result:

- `stage_loaded: true`
- `robot_prim_valid: true`
- output file: `artifacts/phase1/office_nova_isaac_validation.json`

### Bridge Smoke

```bash
bash scripts/run_phase0_bridge_smoke.sh
```

Observed result:

- topic list contained:
  - `/agentslam/camera/depth/image_raw`
  - `/agentslam/camera/rgb/camera_info`
  - `/agentslam/camera/rgb/image_raw`
  - `/agentslam/gt/odom`
  - `/agentslam/imu/data`
  - `/agentslam/semantic_detections`
- sampled detection and odometry messages were written to `artifacts/phase1/`

### Replay Demo

```bash
bash scripts/run_phase1_replay_demo.sh
```

Observed result:

- rosbag info showed `18` messages across `6` topics
- exported replay map contains `3` objects: `chair`, `desk`, `cabinet`
- runtime summary showed:
  - `frames_processed: 3`
  - `skipped_detection_messages: 0`
  - `source_modes_seen: ["bag_replay"]`

### Top-Level Office Demo

```bash
bash scripts/run_phase1_office_demo.sh
```

Observed result:

- script completed successfully
- it re-ran Isaac validation, bridge smoke, and replay demo in order

### Build

```bash
set +u
source /opt/ros/humble/setup.bash
set -u
cd ros_ws
colcon build --packages-select sim_bridge_pkg semantic_mapper_pkg room_graph_pkg semantic_query_pkg nav2_overlay_pkg localization_adapter_pkg eval_tools_pkg
```

Observed result:

- `Summary: 7 packages finished`

### Refs Refresh

```bash
bash scripts/clone_refs.sh > reports/REFS_CLONE_LOG.txt 2>&1
```

Observed result:

- `Successful repositories: 11`
- no failed repositories reported in the final refresh

### GitNexus Status

```bash
timeout 30s npx -y gitnexus@latest list
timeout 30s npx -y gitnexus@latest status .
```

Observed result:

- `AgentSlam` appears in `gitnexus list`
- `Status: up-to-date`
- indexed commit: `3b8df71`

## Facts Only, Not Claims

- no command in this prompt produced a live Isaac ROS image stream from the simulator into the mapper
- all accepted Phase 1 runtime evidence is replay-backed after the headless Isaac asset validation step
