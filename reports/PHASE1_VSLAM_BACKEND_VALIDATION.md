# Phase 1 VSLAM Backend Validation

## Goal

Verify that AgentSlam can replace the `/agentslam/localization/odom` upstream from GT fallback to a real `isaac_ros_visual_slam` backend without changing downstream topic names, while matching the current backend's actual stereo input contract.

## Current Integration Assets

- `ros_ws/launch/phase1_vslam_stereo.launch.py`
- `ros_ws/config/isaac/office_nova_vslam_stereo.yaml`
- `scripts/run_phase1_vslam_live_stereo_smoke.sh`
- `scripts/run_phase1_front_stereo_producer.sh`
- `scripts/stop_phase1_front_stereo_producer.sh`
- `scripts/wait_for_topic_messages.py`
- `scripts/wait_for_stereo_runtime.py`
- `scripts/capture_single_topic_message.py`
- `reports/triage/PHASE1_VSLAM_INPUT_CONTRACT_TRIAGE.md`
- `reports/PHASE1_VSLAM_STEREO_SMOKE_AUTOSTART.md`

## Commands Run

### Minimal Build

```bash
set +u
source /opt/ros/humble/setup.bash
set -u
cd /home/peng/AgentSlam/ros_ws
colcon build --packages-select localization_adapter_pkg
```

Observed result:

- PASS

### Stereo Launch Surface Check

```bash
set +u
source /opt/ros/humble/setup.bash
source /home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash
set -u
ros2 launch /home/peng/AgentSlam/ros_ws/launch/phase1_vslam_stereo.launch.py --show-args
```

Observed result:

- PASS

### Idle Startup Smoke

```bash
set +u
source /opt/ros/humble/setup.bash
source /home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash
set -u
timeout 8s ros2 launch /home/peng/AgentSlam/ros_ws/launch/phase1_vslam_stereo.launch.py
```

Observed result:

- launch starts the `isaac_ros_visual_slam` component container successfully
- the process stays alive for the idle smoke window
- no live odometry is expected in this check because no front-stereo producer was active

### Live Smoke With Autostart

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_vslam_live_stereo_smoke.sh
```

Observed result:

- PASS on validated run snapshots
- when live stereo messages are absent, the script now auto-starts the GS4 front-stereo producer
- the producer now retries cold-start failures until the GS4 foundation contract passes or the attempt budget is exhausted
- the script waits for actual stereo messages and real live-frame files before launching `isaac_ros_visual_slam`
- the validated run captured:
  - `/visual_slam/tracking/odometry`
  - `/agentslam/localization/odom`
  - `/agentslam/localization/status`
- the validated localization runtime summary reported:
  - `primary_messages = 43`
  - `published_messages = 91`
  - `active_source = primary`
- the latest validated rerun summary reported:
  - `primary_messages = 82`
  - `published_messages = 142`
  - `active_source = primary`

### Runtime Flake Check

Observed result:

- a later rerun still showed an intermittent GS4 Isaac worker failure mode
- `camera_info.json` and stereo metadata were present, but `runtime/live_frames/rgb.png` and `rgb_right.png` were missing
- the smoke correctly stopped before launching VSLAM on that invalid runtime state
- this is now treated as an upstream runtime-stability blocker, not an AgentSlam VSLAM-wiring failure

### Contract Triage

Inputs reviewed:

- `/home/peng/GS4/isaac_ros_visual_slam_ws/src/isaac_ros_visual_slam/isaac_ros_visual_slam/src/visual_slam_node.cpp`
- `/home/peng/GS4/isaac_ros_visual_slam_ws/src/isaac_ros_visual_slam/isaac_ros_visual_slam/test/isaac_ros_visual_slam_pol_single_cam_imu.py`
- `/home/peng/GS4/sim_gs4_master/slam/isaac_ros_visual_slam_wrapper/README.md`

Observed result:

- the current backend is stereo-oriented, not RGBD-oriented
- the preferred live contract is the GS4 or Isaac front-stereo topic family
- the earlier RGBD smoke is now treated as an invalid-contract experiment rather than the current acceptance basis

## Evidence

- corrected stereo launch:
  - `ros_ws/launch/phase1_vslam_stereo.launch.py`
- corrected stereo config:
  - `ros_ws/config/isaac/office_nova_vslam_stereo.yaml`
- idle smoke log:
  - `artifacts/phase1/logs/phase1_vslam_stereo_idle_smoke.log`
- contract triage:
  - `reports/triage/PHASE1_VSLAM_INPUT_CONTRACT_TRIAGE.md`
- successful end-to-end smoke snapshot:
  - `artifacts/phase1/success/20260317-135853`
- stability-hardened rerun snapshot:
  - `artifacts/phase1/success/20260317-143724`
- successful smoke report:
  - `reports/PHASE1_VSLAM_STEREO_SMOKE_AUTOSTART.md`
  - `reports/PHASE1_FRONT_STEREO_STABILITY_HARDENING.md`

## Conclusion

- AgentSlam now has both:
  - a stereo-aligned VSLAM bring-up path at the launch and script layer
  - a real successful live stereo VSLAM smoke on this host
- The earlier RGBD trial was the wrong validation contract for the current GS4-hosted backend.
- The next honest blocker is narrower now: GS4 Isaac front-stereo runtime generation is still intermittent across reruns.

## Next Recommended Step

1. Preserve the new smoke autostart flow as the default acceptance path.
2. Triage why `live_isaac_worker.py` sometimes produces stereo metadata but not `live_frames/rgb*.png`.
3. Once the GS4 stereo runtime is stable, use the same smoke to harden repeated-run acceptance.
