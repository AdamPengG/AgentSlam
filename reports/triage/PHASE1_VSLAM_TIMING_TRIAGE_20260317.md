# Phase 1 VSLAM Timing Triage 2026-03-17

## Scope

Use a motion-backed timing capture to separate native Isaac Sim image production, IMU continuity, chassis reference odometry, raw `isaac_ros_visual_slam` odometry, and normalized `/agentslam/localization/odom`.

## Captures Compared

### Capture A: Native Producer Baseline

- artifact dir: `artifacts/phase1/timing_profile/20260317-210538`
- report: `reports/triage/PHASE1_VSLAM_TIMING_PROFILE.md`
- highlights:
  - left image `161` messages in `45s` (`3.58 Hz`)
  - right image `176` messages in `45s` (`3.91 Hz`)
  - front stereo IMU `2280` messages in `45s` (`50.67 Hz`)
  - chassis odom `2306` messages in `45s` (`51.24 Hz`)
  - raw VSLAM odom `125` messages in `45s` (`2.78 Hz`)
  - raw VSLAM odom showed pathological pose jumps up to `39.77 m`

### Capture B: Native Producer Rerun

- artifact dir: `artifacts/phase1/timing_profile/20260317-210909`
- report: `reports/triage/PHASE1_VSLAM_TIMING_PROFILE.md`
- highlights:
  - left image `38` messages in `45s` (`0.84 Hz`)
  - right image `40` messages in `45s` (`0.89 Hz`)
  - front stereo IMU `2392` messages in `45s` (`53.16 Hz`)
  - chassis odom `2397` messages in `45s` (`53.27 Hz`)
  - raw VSLAM odom only `7` messages in `45s` (`0.16 Hz`)
  - raw VSLAM tail silence `8.99 s`
  - normalized localization used only `8` primary messages and republished stale primary pose

### Capture C: Viewport-Updates Experiment

- artifact dir: `artifacts/phase1/timing_profile/20260317-211229`
- change: keep native producer configurable, but test with viewport updates enabled instead of the prior disabled-viewport default
- highlights:
  - left image `34` messages in `45s` (`0.76 Hz`)
  - right image `38` messages in `45s` (`0.84 Hz`)
  - front stereo IMU `2442` messages in `45s` (`54.27 Hz`)
  - chassis odom `2441` messages in `45s` (`54.24 Hz`)
  - raw VSLAM odom `0` messages during the capture window
  - normalized localization odom `0` messages during the capture window

## What This Rules In

- IMU continuity is not the primary failure. `front_stereo_imu/imu` and `/chassis/imu` stay in the `50-54 Hz` range across all captures.
- chassis reference odometry is not the primary failure. `/chassis/odom` stays in the `51-54 Hz` range with low receive-gap jitter.
- localization adapter behavior is not the primary failure. When raw VSLAM odom appears, `/agentslam/localization/odom` republishes it; when raw VSLAM odom disappears, normalized odom also dries up or republishes stale primary state.
- the bottleneck is upstream of normalized localization and strongly coupled to image production plus VSLAM front-end health.

## What This Rules Out

- enabling viewport updates in headless mode did **not** improve image throughput in this workspace state.
- the latest evidence does **not** support blaming missing IMU data for the current failure mode.

## Most Likely Failure Shape

1. `camera_info` continues at roughly `26 Hz`.
2. `image_raw` delivery is much slower and highly bursty, with multi-second gaps.
3. `visual_slam_node` logs frame deltas in the `3.55s` to `9.73s` range on the worst runs.
4. raw VSLAM odom either becomes sparse or vanishes entirely.
5. normalized localization becomes stale because its primary source is sparse or absent.

## Supporting Evidence

- `artifacts/phase1/timing_profile/20260317-210909/timing_summary.json`
- `artifacts/phase1/timing_profile/20260317-211229/timing_summary.json`
- `artifacts/phase1/timing_profile/20260317-210909/vslam_launch.log`
- `artifacts/phase1/timing_profile/20260317-211229/vslam_launch.log`
- `artifacts/phase1/logs/front_stereo_producer/native_isaac_sim.log`

## Conclusion

The current Phase 1 localization-quality blocker is best described as a native Isaac Sim front-stereo image production or delivery problem, not an IMU continuity problem and not a localization-adapter problem. The next fixes should focus on front-hawk image throughput, render-product contract, and any expensive image conversion path between Isaac Sim and `isaac_ros_visual_slam`.
