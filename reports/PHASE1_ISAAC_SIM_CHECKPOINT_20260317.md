# Phase 1 Isaac Sim Checkpoint 2026-03-17

## Intent

Freeze the current Isaac Sim bring-up workstream at a documented checkpoint so the repository can move on without losing the exact recovery point, evidence trail, and current blocker split.

## What Is Already Working

- native Isaac Sim Office + Nova Carter front-stereo producer exists:
  - `scripts/run_phase1_front_stereo_native_producer.sh`
  - `scripts/office_nova_native_ros2_front_stereo.py`
- AgentSlam can launch live stereo `isaac_ros_visual_slam` against that native producer:
  - `scripts/run_phase1_vslam_live_stereo_smoke.sh`
  - `ros_ws/launch/phase1_vslam_stereo.launch.py`
- normalized localization contract remains stable:
  - raw VSLAM odom: `/visual_slam/tracking/odometry`
  - normalized odom: `/agentslam/localization/odom`
- static stereo extrinsics are audited and corrected:
  - `reports/PHASE1_FRONT_STEREO_GEOMETRY_AUDIT.md`
- repeated live-smoke acceptance has already passed on the preferred native path:
  - `reports/PHASE1_VSLAM_STEREO_SMOKE_AUTOSTART.md`
  - `reports/PHASE1_VSLAM_REPEATABILITY_20260317.md`

## What Is Not Ready

- live semantic detections are still not integrated into the accepted Isaac Sim runtime path
- localization quality is not yet acceptable for Phase 2 claims
- the current native image path is bursty enough that smoke-level success overstates actual localization readiness

## Current Best Technical Reading

The latest evidence says the main live-localization blocker is **not** IMU continuity and **not** the localization adapter. The strongest current blocker is the native Isaac Sim front-stereo image path.

Supporting evidence:

- `reports/PHASE1_VSLAM_ACCURACY_EVAL.md`
- `reports/triage/PHASE1_VSLAM_PATH_FOLLOWING_TRIAGE.md`
- `reports/triage/PHASE1_VSLAM_TIMING_TRIAGE_20260317.md`

Current split:

- `front_stereo_imu/imu`, `/chassis/imu`, `/chassis/odom`: stable at roughly `50-54 Hz`
- `front_stereo_camera/*/camera_info`: stable at roughly `26 Hz`
- `front_stereo_camera/*/image_raw`: bursty and often much slower, roughly `0.8-3.9 Hz` in the latest captures
- raw `/visual_slam/tracking/odometry`: sparse or absent when image delivery degrades

## Recovery Point

When we resume Isaac Sim work, start from the native producer image path rather than from geometry, IMU, or localization-adapter debugging.

Resume order:

1. inspect `front_hawk` render-product and image publication settings
2. reduce image-path cost before changing SLAM again
3. rerun `scripts/run_phase1_vslam_timing_profile.sh`
4. rerun `scripts/run_phase1_vslam_accuracy_eval.sh`
5. only after image cadence improves, continue toward live semantic detections

## Operator Entry Points

- smoke:
  - `bash scripts/run_phase1_vslam_live_stereo_smoke.sh`
- timing:
  - `bash scripts/run_phase1_vslam_timing_profile.sh`
- accuracy:
  - `bash scripts/run_phase1_vslam_accuracy_eval.sh`

## Checkpoint Decision

This Isaac Sim workstream is intentionally checkpointed here. Keep the current artifacts and reports as the source of truth, and do not claim live localization quality readiness until the timing and accuracy gates improve.
