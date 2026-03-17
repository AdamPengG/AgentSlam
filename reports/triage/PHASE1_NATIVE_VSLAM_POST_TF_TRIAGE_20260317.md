# PHASE1_NATIVE_VSLAM_POST_TF_TRIAGE_20260317

## What Improved

- The front stereo optical-frame static TF is now aligned to the actual Isaac Sim camera contract.
- Geometry audit moved from a nearly `180 deg` rotation error to `0 deg`.
- Synthetic reprojection gap dropped from "points behind camera" to approximately `1.5e-06 px`.

## Evidence

- Geometry audit report: `/home/peng/AgentSlam/reports/PHASE1_FRONT_STEREO_GEOMETRY_AUDIT.md`
- Fixed reprojection metrics: `/home/peng/AgentSlam/artifacts/phase1/camera_contract/20260317-201003_static_tf_fix/reprojection_metrics.json`
- Fixed overlays:
  - `/home/peng/AgentSlam/artifacts/phase1/camera_contract/20260317-201003_static_tf_fix/left_reprojection_gap.png`
  - `/home/peng/AgentSlam/artifacts/phase1/camera_contract/20260317-201003_static_tf_fix/right_reprojection_gap.png`

## What Did Not Improve Enough

- Native VSLAM accuracy is still not acceptable on the long-route benchmark.
- Compared with the earlier benchmark run:
  - translation RMSE improved from `5.5615 m` to `2.6743 m`
  - yaw RMSE improved from `65.161 deg` to `22.357 deg`
- However, the estimate trajectory still effectively freezes at the origin after normalization:
  - previous estimate path length: `0.000 m`
  - current estimate path length: `0.000 m`

## Latest Accuracy Evidence

- Latest metrics: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/metrics.json`
- Latest matched samples: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/matched_samples.json`
- Latest eval report: `/home/peng/AgentSlam/reports/PHASE1_VSLAM_ACCURACY_EVAL.md`

## Key Runtime Facts

- Localization adapter confirms the normalized odom stayed on the primary VSLAM source:
  - `primary_messages = 12`
  - `published_messages = 103`
  - `active_source = primary`
- This means the adapter did not fall back to GT, but it mostly republished the last available primary pose.

## Producer / Timing Signal

- The native producer log still contains a sustained stream of:
  - `Invalid deltaTime 0.000000`
- This remains the strongest live-system symptom on the producer side and is a plausible cause of weak or stalled VSLAM motion estimates.

## Occupancy / Path Planning Fact

- The path-planning side is not currently blocked by a broken renderer alone.
- Around the current Nova spawn, the Office scene is effectively open:
  - PhysX OMap returns all free cells because the scene exposes almost no useful collision geometry locally.
  - Visual-mesh fallback also finds almost no local environment obstacles after filtering floor meshes and robot self-meshes.
- In the current local planning window, the benchmark path is therefore almost an open-space path with one turn, not a corridor-like obstacle-rich route.

## Supporting Evidence

- Path audit report: `/home/peng/AgentSlam/reports/PHASE1_PATH_TOPDOWN_AUDIT.md`
- Latest planned path:
  - `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/planned_path.json`
  - `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/planned_occupancy_map/debug_topdown.png`
- Stage structure audit:
  - default prim is `/Root`
  - the environment has `155` meshes but only `3` collision-enabled prims in the inspected stage composition

## Most Likely Next Step

1. Investigate native Isaac producer timing health first.
2. Capture live image / camera_info / IMU publish cadence together with raw `/visual_slam/tracking/odometry`.
3. Treat occupancy-rich route selection as a separate benchmark-design task instead of assuming the current spawn neighborhood contains meaningful obstacles.
