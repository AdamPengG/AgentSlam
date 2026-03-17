# Phase 1 Validation

## Commands Run

### Offline Fixture Regression

```bash
bash scripts/run_phase1_fixture.sh
```

### Offline Exploration Regression

```bash
bash scripts/run_phase1_exploration_demo.sh
```

### Localized Mapping Regression

```bash
bash scripts/run_phase1_localized_mapping_demo.sh
```

### Focused Unit Tests

```bash
PYTHONPATH=/home/peng/AgentSlam/ros_ws/src/semantic_mapper_pkg:/home/peng/AgentSlam/ros_ws/src/sim_bridge_pkg \
/usr/bin/python3 -m unittest \
  ros_ws.src.semantic_mapper_pkg.test.test_semantic_mapper \
  ros_ws.src.semantic_mapper_pkg.test.test_runtime_contract \
  ros_ws.src.sim_bridge_pkg.test.test_fixture_io
```

### Isaac Asset Validation

```bash
bash scripts/run_isaac_office_nova.sh --validate-only
```

### Bridge Smoke

```bash
bash scripts/run_phase0_bridge_smoke.sh
```

### Replay Demo

```bash
bash scripts/run_phase1_replay_demo.sh
```

### Top-Level Office Demo

```bash
bash scripts/run_phase1_office_demo.sh
```

### Build

```bash
set +u
source /opt/ros/humble/setup.bash
set -u
cd ros_ws
colcon build --packages-select sim_bridge_pkg semantic_mapper_pkg room_graph_pkg semantic_query_pkg nav2_overlay_pkg localization_adapter_pkg eval_tools_pkg
```

### Stereo VSLAM Launch Surface Check

```bash
set +u
source /opt/ros/humble/setup.bash
source /home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash
set -u
ros2 launch ros_ws/launch/phase1_vslam_stereo.launch.py --show-args
```

### Stereo VSLAM Idle Smoke

```bash
set +u
source /opt/ros/humble/setup.bash
source /home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash
set -u
timeout 8s ros2 launch ros_ws/launch/phase1_vslam_stereo.launch.py
```

### Front-Stereo Producer Strict Revalidation

```bash
START_ATTEMPTS=1 bash scripts/run_phase1_front_stereo_producer.sh
```

### Live Stereo VSLAM Smoke Against A Prestarted Producer

```bash
AUTO_START_PRODUCER=0 bash scripts/run_phase1_vslam_live_stereo_smoke.sh
```

### Native Isaac Sim ROS2 Front-Stereo Producer

```bash
bash scripts/run_phase1_front_stereo_native_producer.sh
```

### Native Isaac Sim ROS2 Live Stereo VSLAM Smoke

```bash
CAPTURE_TIMEOUT_SECONDS=60 WAIT_TIMEOUT_SECONDS=150 \
  bash scripts/run_phase1_vslam_live_stereo_smoke.sh
```

### Native Isaac Sim ROS2 Localization Accuracy Eval

```bash
TARGET_PATH_LENGTH_M=20 EVAL_DURATION_SECONDS=120 FOLLOWER_TIMEOUT_SECONDS=180 \
  bash scripts/run_phase1_vslam_accuracy_eval.sh
```

### Native Isaac Sim ROS2 Timing Profile

```bash
CAPTURE_DURATION_SECONDS=45 WAIT_TIMEOUT_SECONDS=120 \
  bash scripts/run_phase1_vslam_timing_profile.sh
```

## Results

- offline fixture: PASS
- offline exploration demo: PASS
- localized mapping demo: PASS
- focused unit tests: PASS
- headless Isaac Office + Nova validation: PASS
- Phase 0 bridge smoke: PASS
- replay demo: PASS
- top-level office demo: PASS
- colcon build: PASS
- bag replay inspection: PASS
- stereo VSLAM launch surface: PASS
- stereo VSLAM idle smoke: PASS
- full live stereo VSLAM smoke: PASS on validated snapshot
- full live stereo VSLAM smoke stability-hardened rerun: PASS on prior validated snapshot
- front-stereo producer strict readiness rerun: PASS after GS4 worker fix
- full live stereo VSLAM repeated-run stability: PASS for 3 consecutive reruns in the latest session
- native Isaac Sim ROS2 front-stereo producer: PASS
- native Isaac Sim ROS2 live stereo VSLAM smoke: PASS with autostarted native producer
- native Isaac Sim ROS2 localization accuracy eval: FAIL for quality on the occupancy-derived long-route benchmark in the current bring-up
- native Isaac Sim ROS2 timing profile: FAIL for sustained image cadence and sustained raw VSLAM odometry in the current bring-up

## Evidence

- offline map:
  - `artifacts/phase1/synthetic_semantic_map.json`
- offline query outputs:
  - `artifacts/phase1/query_chair.json`
  - `artifacts/phase1/query_table.json`
- offline exploration outputs:
  - `artifacts/phase1/exploration_semantic_map.json`
  - `artifacts/phase1/exploration_progress.json`
  - `artifacts/phase1/exploration_queries/query_chair.json`
  - `artifacts/phase1/exploration_queries/query_cabinet.json`
  - `artifacts/phase1/exploration_queries/query_sofa.json`
- localized mapping outputs:
  - `artifacts/phase1/office_nova_localization_runtime.json`
  - `artifacts/phase1/office_nova_localized_occupancy.json`
  - `artifacts/phase1/office_nova_localized_occupancy_runtime.json`
  - `artifacts/phase1/office_nova_localized_semantic_map.json`
  - `artifacts/phase1/localized_queries/query_chair.json`
  - `artifacts/phase1/localized_queries/query_desk.json`
  - `artifacts/phase1/localized_queries/query_cabinet.json`
- Isaac validation summary:
  - `artifacts/phase1/office_nova_isaac_validation.json`
- bridge smoke evidence:
  - `artifacts/phase1/phase0_bridge_topics.txt`
  - `artifacts/phase1/phase0_bridge_detection_sample.txt`
  - `artifacts/phase1/phase0_bridge_odom_sample.txt`
- replay bag:
  - `artifacts/phase1/office_nova_replay_bag`
- replay map:
  - `artifacts/phase1/office_nova_replay_semantic_map.json`
- replay runtime summary:
  - `artifacts/phase1/office_nova_replay_semantic_map_runtime.json`
- replay query outputs:
  - `artifacts/phase1/replay_queries/query_chair.json`
  - `artifacts/phase1/replay_queries/query_desk.json`
  - `artifacts/phase1/replay_queries/query_cabinet.json`
  - `artifacts/phase1/query_chair_replay_cli.json`
  - `artifacts/phase1/query_cabinet_replay_cli.json`
- VSLAM launch and triage evidence:
  - `artifacts/phase1/logs/phase1_vslam_stereo_idle_smoke.log`
  - `reports/PHASE1_VSLAM_BACKEND_VALIDATION.md`
  - `reports/PHASE1_VSLAM_STEREO_SMOKE_AUTOSTART.md`
  - `reports/PHASE1_VSLAM_REPEATABILITY_20260317.md`
  - `reports/PHASE1_NATIVE_ISAAC_ROS2_PRODUCER.md`
  - `reports/PHASE1_VSLAM_ACCURACY_EVAL.md`
  - `reports/triage/PHASE1_VSLAM_TIMING_TRIAGE_20260317.md`
  - `reports/triage/PHASE1_VSLAM_TIMING_PROFILE.md`
  - `reports/triage/PHASE1_VSLAM_INPUT_CONTRACT_TRIAGE.md`
  - `reports/triage/PHASE1_FRONT_STEREO_NUMPY_PAD_ROOT_CAUSE.md`
- successful live stereo VSLAM snapshot:
  - `artifacts/phase1/success/20260317-135853`
  - `artifacts/phase1/success/20260317-143724`
  - `reports/PHASE1_FRONT_STEREO_STABILITY_HARDENING.md`

## Limits

- live localization now has a validated native Isaac Sim ROS2 stereo path, but live semantic detections are still not part of the accepted runtime loop
- the normalized localization contract is working, but the preferred VSLAM path currently depends on an external GS4 overlay and a live front-stereo Isaac or GS4 producer rather than an AgentSlam-owned runtime
- the earlier RGBD VSLAM trial was retired after contract triage showed the current backend is stereo-oriented
- VSLAM odometry is now artifact-validated for `/agentslam/localization/odom` on the snapshot under `artifacts/phase1/success/20260317-135853`
- the current trajectory-error evaluation now uses an Isaac Sim occupancy-derived `single_goal` start/end route of `20.002m` with `1` planned turn, and the latest full run recorded `6.554m` of executed reference motion while `/agentslam/localization/odom` still collapsed to `0.000m`, so smoke-level success still overstates localization quality
- the newest motion-mode triage shows that native VSLAM can move under straight-line probes, but the waypoint-following benchmark still compresses raw and normalized VSLAM odometry far below the executed `/chassis/odom` path, see `reports/triage/PHASE1_VSLAM_PATH_FOLLOWING_TRIAGE.md`
- the newest timing triage shows the current native path is not primarily limited by IMU or chassis odometry continuity; instead, the front stereo `image_raw` streams are bursty and much slower than `camera_info`, and raw VSLAM odometry dries up when those image gaps widen, see `reports/triage/PHASE1_VSLAM_TIMING_TRIAGE_20260317.md`
- repeated-run stability is closed for the native producer smoke path, but the legacy GS4 file bridge remains a separate fallback path with its own historical flake
- the new producer retry path reduces operator-facing flake by rejecting and retrying bad cold starts before handing the runtime to VSLAM
- the latest strict producer-only rerun now passes again after the GS4 worker fix, and the smoke path remains protected by the same retry plus health-gate orchestration
- the long-route benchmark currently compares against executed `/chassis/odom` rather than the nominal route itself, which is intentional so controller tracking error is not miscounted as SLAM error
- TF and `/clock` are still documented bridge expectations rather than artifacts produced by the replay demo
