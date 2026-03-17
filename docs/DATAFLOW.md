# AgentSlam Dataflow Draft

## Phase 1 Executed Pipeline

1. `scripts/run_isaac_office_nova.sh` validates the release Isaac Python entrypoint by loading `office.usd` and adding `nova_carter.usd` headlessly.
2. `scripts/run_phase0_bridge_smoke.sh` publishes the agreed topic family through `sim_bridge_pkg.fixture_replay_publisher`.
3. `scripts/run_phase1_replay_demo.sh` records those topics into `artifacts/phase1/office_nova_replay_bag`.
4. The same script replays the bag with `ros2 bag play`.
5. `localization_adapter_pkg.ros_node` republishes normalized localization odometry on `/agentslam/localization/odom`, using GT fallback on the replay path and a VSLAM primary source when available.
6. `semantic_mapper_pkg.ros_node` consumes camera info, RGB, depth, IMU, normalized localization odometry, and detection envelopes.
7. `SemanticMapBuilder` projects detections into world centroids using the normalized localization pose and merges nearby objects by label.
8. `nav2_overlay_pkg.localized_mapping` builds a lightweight 2D occupancy-style grid from the same localized observations.
9. The pipeline exports:
   - `artifacts/phase1/office_nova_replay_semantic_map.json`
   - `artifacts/phase1/replay_queries/query_*.json`
   - `artifacts/phase1/office_nova_replay_semantic_map_runtime.json`

## Offline Regression Path

1. `scripts/run_phase1_fixture.sh` loads `fixtures/semantic_mapping/synthetic_gt_pose_scene.json`.
2. The mapper runs in `fixture` mode.
3. Outputs land in:
   - `artifacts/phase1/synthetic_semantic_map.json`
   - `artifacts/phase1/query_chair.json`
   - `artifacts/phase1/query_table.json`
   - optional spatial query outputs from the query CLI when requested

## Offline Exploration Regression Path

1. `scripts/run_phase1_exploration_demo.sh` loads `fixtures/semantic_mapping/exploration_gt_pose_scene.json`.
2. `nav2_overlay_pkg.exploration_demo` scores candidate viewpoints by semantic gain with a small travel penalty.
3. The chosen route is replayed through `SemanticMapBuilder`.
4. Outputs land in:
   - `artifacts/phase1/exploration_semantic_map.json`
   - `artifacts/phase1/exploration_progress.json`
   - `artifacts/phase1/exploration_queries/query_*.json`

## Localized Mapping Regression Path

1. `scripts/run_phase1_localized_mapping_demo.sh` starts:
   - `localization_adapter_pkg.ros_node`
   - `nav2_overlay_pkg.localized_mapping`
   - `semantic_mapper_pkg.ros_node`
   - `sim_bridge_pkg.fixture_replay_publisher`
2. The localization adapter normalizes odometry onto `/agentslam/localization/odom`.
3. The geometric mapper converts localized detection rays into a small occupancy-style 2D grid.
4. The semantic mapper fuses the same localized detections into the semantic object map.
5. Outputs land in:
   - `artifacts/phase1/office_nova_localization_runtime.json`
   - `artifacts/phase1/office_nova_localized_occupancy.json`
   - `artifacts/phase1/office_nova_localized_occupancy_runtime.json`
   - `artifacts/phase1/office_nova_localized_semantic_map.json`
   - `artifacts/phase1/localized_queries/query_*.json`

## VSLAM Backend Smoke Path

1. `scripts/run_phase1_vslam_live_stereo_smoke.sh` sources:
   - `/opt/ros/humble/setup.bash`
   - `/home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash`
2. By default, the smoke autostarts `scripts/run_phase1_front_stereo_native_producer.sh` when stereo topics are absent.
3. The native producer loads Office + Nova Carter directly inside Isaac Sim and keeps only the front stereo pair enabled while disabling the extra hawk cameras and lidar render products.
4. The preferred native topic contract is:
   - `/front_stereo_camera/left/image_raw`
   - `/front_stereo_camera/left/camera_info`
   - `/front_stereo_camera/right/image_raw`
   - `/front_stereo_camera/right/camera_info`
   - `/tf_static`
5. AgentSlam supplies static extrinsics for `base_link -> chassis_link -> front_stereo_camera_*_optical`; Isaac Sim does not own the SLAM map or odom transform chain.
6. `ros_ws/launch/phase1_vslam_stereo.launch.py` starts `isaac_ros_visual_slam` against that stereo contract with `rectified_images=false` and `base_frame=chassis_link`.
7. `isaac_ros_visual_slam` publishes raw odometry on `/visual_slam/tracking/odometry`.
8. `localization_adapter_pkg.ros_node` republishes that stream as `/agentslam/localization/odom`.
9. The smoke exports:
   - `artifacts/phase1/office_nova_vslam_live_raw_odom.txt`
   - `artifacts/phase1/office_nova_vslam_live_localization_odom.txt`
   - `artifacts/phase1/office_nova_vslam_live_status.txt`
   - `artifacts/phase1/office_nova_vslam_live_localization_runtime.json`
10. The previous GS4 file bridge and RGBD reference-bag trials are retained only as fallback or historical evidence; they are no longer the preferred acceptance path for the current backend.

## Topic-Level Flow

1. `sim_bridge_pkg.fixture_replay_publisher`
   - publishes `sensor_msgs/msg/Image`, `sensor_msgs/msg/CameraInfo`, `sensor_msgs/msg/Imu`, `nav_msgs/msg/Odometry`, and `std_msgs/msg/String`
2. `localization_adapter_pkg.ros_node`
   - chooses between preferred odometry and GT fallback
   - republishes a stable localization topic for downstream consumers
3. `semantic_mapper_pkg.ros_node`
   - caches latest intrinsics and pose
   - treats the detection envelope as the frame trigger
   - buffers an early detection envelope until pose and camera info are both ready
   - finalizes after `expected_frames` or idle timeout
4. `nav2_overlay_pkg.localized_mapping`
   - projects localized detections into 2D rays
   - exports an occupancy-style grid plus runtime metrics
5. query consumers
   - read exported JSON rather than depending on a live service surface
   - can filter by label, reference point, radius, minimum observations, and result limit

## Sensor Policy

- required for the executed Phase 1 path: RGB, camera info, IMU, GT odometry as raw fallback, normalized localization odometry for downstream consumers
- optional but available in replay: depth image
- intentionally disabled by default: LiDAR, point cloud, and laser scan requirements

## Dependency Flow

- `IsaacSim-ros_workspaces` and `message_filters` are now available locally for later bridge refinement
- the Prompt 4 accepted path does not yet depend on them at runtime
- `DROID-SLAM`, `MASt3R-SLAM`, `HOV-SG`, and `concept-graphs` remain deferred from the runtime loop
- `isaac_ros_visual_slam` is currently available through an external GS4 overlay and can drive the normalized localization contract during smoke validation
- `isaac_ros_nvblox` is still not part of the AgentSlam-owned runtime path

## Open Questions

- when the offline exploration scaffold should become a live Nav2-driven execution path
- when the preferred odometry source should switch from GT fallback to a real VSLAM backend in this workspace
- when the live Isaac Office + Nova front-stereo producer should become a routine validation source instead of a manual prerequisite
- when the live Isaac ROS bridge is added, should detection envelopes continue as JSON over `std_msgs/msg/String` or become a custom type
- whether TF and `/clock` should be promoted from reserved expectations into replay acceptance gates

## Prompt 5 Ops Flow

1. A GitHub workflow or manual shell run invokes one of:
   - `scripts/ops/phase1_ci_suite.sh`
   - `scripts/ops/nightly_phase1_eval.sh`
   - `scripts/ops/refresh_plan.sh`
   - `scripts/ops/triage_failure.sh`
2. For nightly runs, `scripts/ops/nightly_phase1_eval.sh` now precomputes:
   - `nightly_summary_inputs.md`
   - `nightly_delta.md`
   - shell fallback summary and handoff files
3. `scripts/ops/check_codex_auth.sh` verifies local Codex readiness when a Codex-backed summary or triage task is requested.
4. `scripts/ops/with_codex_lock.sh` serializes `codex exec` access to the local ChatGPT-managed auth state.
5. `scripts/ops/run_codex_exec.sh` snapshots the checked-in prompt, appends runtime context, runs `codex exec`, and stores:
   - final report under `reports/`
   - JSONL event log under `artifacts/ops/` or `artifacts/nightly/`
   - stderr log and metadata under the same artifact root
6. If the Codex summary path succeeds, it overwrites the shell fallback report; if it fails or times out, the shell fallback remains in place so operator-visible summary and handoff files still exist.
7. Operator-facing results are read from:
   - `reports/nightly/`
   - `reports/plan_refresh/`
   - `reports/triage/`

## OpenClaw Control-Plane Flow

1. Repo-side source lives under `ops/openclaw/src/conf.d/` and `ops/openclaw/src/shared-skills/`.
2. `ops/openclaw/bin/render_openclaw.sh` renders a flat runtime config from the split fragments.
3. `ops/openclaw/bin/validate_openclaw.sh` renders into a temporary `HOME` and runs `openclaw config validate`.
4. `ops/openclaw/bin/deploy_openclaw.sh` performs a backup-first deploy into `~/.openclaw`.
5. OpenClaw agents call bounded wrapper scripts under `ops/openclaw/bin/` instead of broad shell commands.
6. Wrapper scripts delegate into existing `scripts/` and `scripts/ops/` entrypoints where possible.
7. Status, security, Telegram, cron, and ACP findings are persisted under `reports/openclaw/`.
8. The completion gate decides whether to notify the operator and stop at `awaiting_user_review`.
