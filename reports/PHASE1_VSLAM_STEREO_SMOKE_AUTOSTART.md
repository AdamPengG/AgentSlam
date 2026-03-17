# Phase 1 Stereo VSLAM Smoke Autostart

## Goal

Turn `scripts/run_phase1_vslam_live_stereo_smoke.sh` into a self-bootstrapping live VSLAM smoke that can:

- auto-start the GS4 Isaac front-stereo producer when live stereo messages are absent
- wait for material stereo runtime readiness instead of only topic-name visibility
- launch `isaac_ros_visual_slam` only after the runtime contract is ready
- prove that `/agentslam/localization/odom` can switch to the real VSLAM upstream

## Key Changes

- `scripts/run_phase1_vslam_live_stereo_smoke.sh`
  - auto-starts the GS4 front-stereo producer by default
  - waits for real stereo messages, not just topic graph entries
  - waits for `camera_info.json` plus `live_frames/{rgb.png,rgb_right.png}` before launching VSLAM
  - escalates process shutdown so the smoke exits cleanly
- `scripts/run_phase1_front_stereo_producer.sh`
  - starts the GS4 bridge earlier
  - requires the GS4 foundation contract to pass before declaring the producer ready
  - retries cold start up to 5 attempts by default
  - disowns successful background jobs so the bootstrap shell can exit cleanly
- `scripts/wait_for_topic_messages.py`
  - blocks until actual ROS messages are received on the requested topics
- `scripts/wait_for_stereo_runtime.py`
  - blocks until the GS4 runtime has both enabled stereo metadata and real live-frame files

## Successful Validation

### Build Gate

```bash
cd /home/peng/AgentSlam/ros_ws
colcon build --packages-select localization_adapter_pkg
```

Observed result:

- PASS

### End-to-End Smoke

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_vslam_live_stereo_smoke.sh
```

Observed result:

- PASS
- the script auto-started the GS4 front-stereo producer
- `isaac_ros_visual_slam` initialized successfully on the valid stereo contract
- `/visual_slam/tracking/odometry` was captured
- `/agentslam/localization/odom` was captured
- `/agentslam/localization/status` reported `active_source=primary`
- localization runtime summary reported:
  - `primary_messages = 43`
  - `published_messages = 91`
  - `active_source = primary`

### Stability-Hardened Rerun

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_vslam_live_stereo_smoke.sh
```

Observed result:

- PASS
- the hardened producer path rejected bad cold starts and retried automatically
- latest validated localization runtime summary reported:
  - `primary_messages = 82`
  - `published_messages = 142`
  - `active_source = primary`

## Success Evidence

- snapshot directory:
  - `artifacts/phase1/success/20260317-135853`
- latest rerun snapshot:
  - `artifacts/phase1/success/20260317-143724`
- raw VSLAM odometry sample:
  - `artifacts/phase1/success/20260317-135853/office_nova_vslam_live_raw_odom.txt`
- normalized localization odometry sample:
  - `artifacts/phase1/success/20260317-135853/office_nova_vslam_live_localization_odom.txt`
- localization runtime summary:
  - `artifacts/phase1/success/20260317-135853/office_nova_vslam_live_localization_runtime.json`
- localization status sample:
  - `artifacts/phase1/success/20260317-135853/office_nova_vslam_live_status.txt`
- VSLAM launch log:
  - `artifacts/phase1/success/20260317-135853/phase1_vslam_live_stereo_launch.log`
- localization adapter log:
  - `artifacts/phase1/success/20260317-135853/phase1_vslam_live_stereo_localization.log`
- GS4 worker and bridge logs:
  - `artifacts/phase1/success/20260317-135853/live_isaac_worker.log`
  - `artifacts/phase1/success/20260317-135853/stereo_bridge.log`
  - `artifacts/phase1/success/20260317-135853/foundation_check.txt`
  - `artifacts/phase1/success/20260317-143724/live_isaac_worker.log`
  - `artifacts/phase1/success/20260317-143724/stereo_bridge.log`
  - `artifacts/phase1/success/20260317-143724/foundation_check.txt`

## Remaining Runtime Risk

A later rerun still showed an intermittent GS4 Isaac worker failure mode:

- `camera_info.json` was produced and `isaac_front_stereo.enabled=true`
- but `runtime/live_frames/rgb.png` and `rgb_right.png` were missing
- the foundation contract therefore failed on missing live-frame files

That means the AgentSlam smoke orchestration is now working, but the upstream Isaac worker remains intermittently unstable across reruns.

The latest hardening pass improves the operator path anyway:

- bad producer starts are now retried automatically
- the full smoke passed again on snapshot `20260317-143724`
- the remaining instability is narrower and more clearly isolated to the upstream GS4 runtime

## Conclusion

- AgentSlam now has a real, successful, live stereo VSLAM smoke on this host.
- The remaining blocker is no longer the smoke entrypoint or topic-contract wiring.
- The remaining blocker is GS4 Isaac front-stereo runtime stability across repeated runs.
