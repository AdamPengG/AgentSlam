# Phase 1 VSLAM Input Contract Triage

## Failing Stage

```bash
bash scripts/run_phase1_vslam_reference_smoke.sh
```

## Failure Category

- artifact contract drift
- operator/setup gap

## What Was Actually Wrong

- The failing path assumed the local GS4-hosted `isaac_ros_visual_slam` backend supported an AgentSlam-owned RGBD contract.
- Local source inspection showed the current backend subscribes only to:
  - `visual_slam/image_0`
  - `visual_slam/camera_info_0`
  - `visual_slam/image_1`
  - `visual_slam/camera_info_1`
  - optional `visual_slam/imu`
- The packaged tests and launch files in `/home/peng/GS4/isaac_ros_visual_slam_ws/src/isaac_ros_visual_slam` are all stereo-oriented, not RGBD-oriented.
- GS4's live Isaac + Nova bridge already standardizes the expected upstream contract as:
  - `/front_stereo_camera/left/image_rect_color`
  - `/front_stereo_camera/left/camera_info`
  - `/front_stereo_camera/right/image_rect_color`
  - `/front_stereo_camera/right/camera_info`

## Conclusion

- The previous RGBD smoke failure should not be treated as authoritative evidence that this machine cannot run cuVSLAM.
- The more credible diagnosis is that AgentSlam was validating the backend with the wrong input contract for this backend version.

## Minimum Next Step

1. Prefer the new stereo launch path:
   - `ros_ws/launch/phase1_vslam_stereo.launch.py`
2. Use the live stereo smoke once the Isaac/GS4 front-stereo producer is running:
   - `scripts/run_phase1_vslam_live_stereo_smoke.sh`
3. Only if the same failure reproduces on that valid stereo contract should we reopen the deeper GPU/runtime hypothesis.
