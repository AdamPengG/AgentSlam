# Phase 1 Native Isaac Sim ROS2 Producer

## Goal

Validate that AgentSlam can prefer a native Isaac Sim ROS2 Office + Nova Carter front-stereo producer over the legacy GS4 file bridge for live stereo VSLAM localization.

## Commands Run

### Producer-only bring-up

```bash
bash scripts/run_phase1_front_stereo_native_producer.sh
```

### Topic audit while producer was live

```bash
source /opt/ros/humble/setup.bash
ros2 topic list | sort
```

### Prestarted native producer smoke

```bash
PRODUCER_MODE=isaac_native_ros2 AUTO_START_PRODUCER=0 \
  CAPTURE_TIMEOUT_SECONDS=60 WAIT_TIMEOUT_SECONDS=120 \
  bash scripts/run_phase1_vslam_live_stereo_smoke.sh
```

### Clean autostart native smoke

```bash
CAPTURE_TIMEOUT_SECONDS=60 WAIT_TIMEOUT_SECONDS=150 \
  bash scripts/run_phase1_vslam_live_stereo_smoke.sh
```

### Supporting validation

```bash
source /opt/ros/humble/setup.bash
cd ros_ws
colcon build --packages-select localization_adapter_pkg
```

```bash
source /opt/ros/humble/setup.bash
source /home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash
ros2 launch ros_ws/launch/phase1_vslam_stereo.launch.py --show-args
```

## Results

- native Isaac Sim producer bring-up: PASS
- native topic contract: PASS
- prestarted native VSLAM smoke: PASS
- autostart native VSLAM smoke: PASS
- localization adapter runtime: PASS with `active_source=primary`
- cleanup after autostart smoke: PASS

## Observed Native Topic Contract

### Required topics observed

- `/front_stereo_camera/left/image_raw`
- `/front_stereo_camera/left/camera_info`
- `/front_stereo_camera/right/image_raw`
- `/front_stereo_camera/right/camera_info`
- `/tf_static`

### Auxiliary topics still present but not required by AgentSlam

- `/chassis/odom`
- `/tf`
- `/back_stereo_imu/imu`
- `/chassis/imu`
- `/front_stereo_imu/imu`
- `/left_stereo_imu/imu`
- `/right_stereo_imu/imu`

The current Phase 1 localization acceptance path ignores those auxiliary topics and only depends on stereo images, camera info, and static extrinsics.

## Key Runtime Facts

- static extrinsics are supplied by AgentSlam-owned `static_transform_publisher` processes
- native VSLAM smoke now defaults to `PRODUCER_MODE=isaac_native_ros2`
- native mode uses:
  - `left_image_topic=/front_stereo_camera/left/image_raw`
  - `right_image_topic=/front_stereo_camera/right/image_raw`
  - `rectified_images=false`
  - `base_frame=chassis_link`
- `office_nova_vslam_live_localization_runtime.json` recorded:
  - `active_source=primary`
  - `primary_messages=73`
  - `fallback_messages=0`
  - `published_messages=124`

## Evidence

- producer logs:
  - `artifacts/phase1/logs/front_stereo_producer/native_isaac_sim.log`
  - `artifacts/phase1/logs/front_stereo_producer/native_cmd_vel.log`
  - `artifacts/phase1/logs/front_stereo_producer/native_static_tf.log`
- smoke outputs:
  - `artifacts/phase1/office_nova_vslam_live_raw_odom.txt`
  - `artifacts/phase1/office_nova_vslam_live_localization_odom.txt`
  - `artifacts/phase1/office_nova_vslam_live_status.txt`
  - `artifacts/phase1/office_nova_vslam_live_localization_runtime.json`

## Conclusion

The preferred live localization path is now the native Isaac Sim ROS2 front-stereo producer, not the GS4 file bridge. The remaining runtime gap for Phase 1 is no longer live localization; it is live semantic detections and full live semantic mapping on top of the now-validated native localization path.
