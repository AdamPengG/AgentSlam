# Phase 0 Bringup Status

## Current Artifacts

- `ros_ws/launch/phase0_bringup.launch.py`
- `ros_ws/launch/phase1_office_semantic_mapping.launch.py`
- `ros_ws/config/isaac/phase0_bridge.yaml`
- `ros_ws/config/isaac/office_nova_phase1.yaml`
- `scripts/run_isaac_office_nova.sh`
- `scripts/run_phase0_bridge_smoke.sh`

## Current Strategy

- validate the preferred Isaac release launcher and Office + Nova asset pair headlessly first
- use a replay-backed ROS path as the Prompt 4 acceptance route
- keep the bridge contract focused on RGB, depth, camera info, IMU, GT pose, and semantic detections
- leave live TF and `/clock` integration to the next bridge refinement pass

## Selected Defaults

- preferred launcher:
  - `/home/peng/IsaacSim/_build/linux-x86_64/release/isaac-sim.sh`
- preferred Python:
  - `/home/peng/IsaacSim/_build/linux-x86_64/release/python.sh`
- preferred scene:
  - `/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd`
- preferred robot:
  - `/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd`

## Current State

- headless scene plus robot validation: complete
- replay-backed bridge smoke: complete
- replay-backed office demo: complete
- live Isaac ROS topic bring-up: not yet executed in this prompt
- blocker level: non-fatal for Phase 1 review because the replay path is now real and repeatable
