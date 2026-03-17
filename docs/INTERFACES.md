# AgentSlam Interface Draft

## Non-Negotiable Constraints

- use standard ROS 2 messages whenever possible
- start with GT pose as the localization source
- visual plus IMU remains the default sensing policy
- LiDAR is out of scope by default for Phase 1
- prefer the locally validated Office + Nova Carter pair

## Phase 1 Bridge Contract

### Validated Topic Set

- `/agentslam/camera/rgb/image_raw`
  - type: `sensor_msgs/msg/Image`
- `/agentslam/camera/rgb/camera_info`
  - type: `sensor_msgs/msg/CameraInfo`
- `/agentslam/camera/depth/image_raw`
  - type: `sensor_msgs/msg/Image`
  - note: optional at the policy level, but present in the replay harness
- `/agentslam/imu/data`
  - type: `sensor_msgs/msg/Imu`
- `/agentslam/gt/odom`
  - type: `nav_msgs/msg/Odometry`
- `/agentslam/localization/odom`
  - type: `nav_msgs/msg/Odometry`
  - note: normalized localization output, now ready to prefer `isaac_ros_visual_slam` odometry when an overlay is sourced, with GT retained as fallback
- `/agentslam/localization/status`
  - type: `std_msgs/msg/String`
  - payload: JSON status describing the active odometry source
- `/agentslam/semantic_detections`
  - type: `std_msgs/msg/String`
  - payload: JSON detection envelope

### Detection Envelope

`/agentslam/semantic_detections` carries JSON with:

- `frame_id`
- `source_mode`
- `detections`
  - each detection contains `label`, `pixel_x`, `pixel_y`, `depth_m`, `confidence`

This keeps Phase 1 on standard ROS transport while avoiding custom message debt too early.

### Reserved But Not Yet Acceptance-Critical

- `/clock`
- `/tf`
- `/tf_static`

These remain part of the live bridge target, but Prompt 4 acceptance does not depend on them because the validated chain is replay-backed.

## Live Stereo VSLAM Input Contract

### Preferred Upstream Topics

- `/front_stereo_camera/left/image_rect_color`
  - type: `sensor_msgs/msg/Image`
- `/front_stereo_camera/left/camera_info`
  - type: `sensor_msgs/msg/CameraInfo`
- `/front_stereo_camera/right/image_rect_color`
  - type: `sensor_msgs/msg/Image`
- `/front_stereo_camera/right/camera_info`
  - type: `sensor_msgs/msg/CameraInfo`

### Notes

- this is the preferred `isaac_ros_visual_slam` input contract for the current GS4-hosted backend
- the old AgentSlam-owned RGBD VSLAM trial is no longer the preferred path for this backend version
- downstream AgentSlam consumers should continue to depend only on `/agentslam/localization/odom`

## Mapping-Facing Contract

### Supported Data Source Modes

- `fixture`
- `bag_replay`
- `live_isaac`

### Required Inputs For Replay And Live Modes

- RGB image
- camera info
- IMU
- normalized localization odometry via `/agentslam/localization/odom`
- semantic detections envelope

### Outputs

- semantic map JSON under `artifacts/phase1/`
- localized occupancy-style map JSON under `artifacts/phase1/`
- query result JSON files under `artifacts/phase1/`
- runtime summary JSON for each executed mapper run
- exploration progress JSON for offline exploration-backed runs

### Query Contract

The exported-map query layer supports:

- label substring search
- optional reference point via `near_x` and `near_y`
- optional `radius_m` filtering around that reference point
- optional `min_observations` gating
- optional `limit` for bounded result sets

Each query response includes `filters`, `match_count`, `returned_match_count`, and `matches`.

## Localization Adapter Contract

### Current Phase 1 Entry Point

- module: `localization_adapter_pkg.ros_node`
- primary topic default: `/visual_slam/tracking/odometry`
- fallback topic default: `/agentslam/gt/odom`
- normalized output: `/agentslam/localization/odom`
- VSLAM launch entry: `ros_ws/launch/phase1_vslam_stereo.launch.py`
- backend smoke entry: `scripts/run_phase1_vslam_live_stereo_smoke.sh`

### Behavioral Notes

- consumer nodes should subscribe to `/agentslam/localization/odom` instead of wiring directly to a raw odometry producer
- the adapter can now consume a real stereo `isaac_ros_visual_slam` backend from a sourced overlay without changing downstream mappers
- the preferred live VSLAM expectation is the front-stereo Isaac or GS4 topic family rather than the earlier RGBD trial
- status is exported on `/agentslam/localization/status` so operators can confirm whether the system is running on preferred or fallback odometry

## Localized Geometric Map Contract

### Current Phase 1 Entry Point

- script: `scripts/run_phase1_localized_mapping_demo.sh`
- module: `nav2_overlay_pkg.localized_mapping`

### Inputs

- camera info
- normalized localization odometry
- semantic detection envelope with depth-bearing observations

### Outputs

- `artifacts/phase1/office_nova_localized_occupancy.json`
- `artifacts/phase1/office_nova_localized_occupancy_runtime.json`
- `artifacts/phase1/office_nova_localized_semantic_map.json`
- `artifacts/phase1/office_nova_localization_runtime.json`

### Behavioral Notes

- the geometric map is a lightweight 2D occupancy-style grid derived from localized detection rays
- this is not a full `nvblox` or dense TSDF integration yet
- the semantic map now rides on the same normalized localization topic as the geometric map

## Exploration Scaffold Contract

### Current Phase 1 Entry Point

- script: `scripts/run_phase1_exploration_demo.sh`
- module: `nav2_overlay_pkg.exploration_demo`

### Inputs

- fixture JSON with:
  - camera intrinsics
  - ordered candidate frames
  - GT pose per frame
  - semantic detections per frame

### Outputs

- `artifacts/phase1/exploration_semantic_map.json`
- `artifacts/phase1/exploration_progress.json`
- `artifacts/phase1/exploration_queries/query_*.json`

### Behavioral Notes

- the exploration scaffold does not publish or consume live ROS navigation topics
- route selection is currently offline and artifact-backed
- semantic map fusion still uses the same mapper contract as fixture and replay modes

## Asset-Level Assumptions

- launcher: `/home/peng/IsaacSim/_build/linux-x86_64/release/isaac-sim.sh`
- Python entrypoint: `/home/peng/IsaacSim/_build/linux-x86_64/release/python.sh`
- scene: `/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd`
- robot: `/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd`

## Open Items

- add a real live Isaac ROS bridge that publishes the same topic family
- replace the external VSLAM overlay dependency with an AgentSlam-owned workspace or formal installation prerequisite
- upgrade the offline exploration scaffold into a live exploration and navigation loop
- decide whether TF and `/clock` should become mandatory for replay acceptance in Phase 2
- decide whether semantic outputs should later grow a service surface in addition to JSON artifacts

## Ops Automation Contract

### Nightly Inputs

- fixture baseline:
  - `fixtures/semantic_mapping/synthetic_gt_pose_scene.json`
- Phase 1 runner scripts:
  - `scripts/run_phase1_fixture.sh`
  - `scripts/run_phase0_bridge_smoke.sh`
- Phase 1 build and unit test commands through `scripts/ops/phase1_ci_suite.sh`

### Nightly Outputs

- suite reports:
  - `reports/nightly/phase1_suite_<timestamp>.md`
  - `reports/nightly/latest_suite.md`
- summary reports:
  - `reports/nightly/nightly_phase1_eval_<timestamp>.md`
  - `reports/nightly/latest_summary.md`
- handoff reports:
  - `reports/nightly/nightly_handoff_<timestamp>.md`
  - `reports/nightly/latest_handoff.md`
- machine artifacts:
  - `artifacts/nightly/<timestamp>/`
  - `artifacts/nightly/<timestamp>/nightly_summary_inputs.md`
  - `artifacts/nightly/<timestamp>/nightly_delta.md`

### Codex Exec Wrapper Contract

- prompt templates live under `prompts/exec/`
- wrapper entrypoint is `scripts/ops/run_codex_exec.sh`
- lock wrapper is `scripts/ops/with_codex_lock.sh`
- auth preflight is `scripts/ops/check_codex_auth.sh`
- default behavior is report-writing and log capture, not direct source editing
- nightly summary and handoff generation now use a shell-produced fallback plus a Codex overwrite path

## OpenClaw Control Plane Contract

### Repo-side source of truth

- `ops/openclaw/src/conf.d/*.json5`: versioned OpenClaw config fragments
- `ops/openclaw/src/shared-skills/`: OpenClaw-shared skill source
- `ops/openclaw/bin/`: the only approved high-frequency OpenClaw wrapper entrypoints

### Deployment contract

- `ops/openclaw/bin/render_openclaw.sh` flattens repo-side fragments into one runtime config
- `ops/openclaw/bin/deploy_openclaw.sh` backs up the live config before writing
- `ops/openclaw/bin/validate_openclaw.sh` validates the rendered config in a temporary home

### Operator-facing status contract

- live state reports live under `reports/openclaw/`
- completion gating writes `reports/openclaw/PHASE1_COMPLETION_GATE.md`
- Telegram notifications are sent only through `ops/openclaw/bin/agentslam_notify_telegram.sh`
