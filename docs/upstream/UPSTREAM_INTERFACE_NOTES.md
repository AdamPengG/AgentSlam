# Upstream Interface Notes

## Clone Status Snapshot

- cloned successfully:
  - `navigation2`
  - `slam_toolbox`
  - `vision_opencv`
  - `OneMap`
  - `concept-graphs`
  - `MASt3R-SLAM`
  - `GitNexus`
- clone failed in the current environment:
  - `IsaacSim-ros_workspaces`
  - `message_filters`
  - `HOV-SG`
  - `DROID-SLAM`

## Interface Notes By Repository

### navigation2

- likely entry surface:
  - `nav2_bringup` and related launch/config packages
- useful interface takeaways:
  - goal execution boundaries
  - behavior tree extension seams
  - costmap and controller package boundaries
- AgentSlam use:
  - reserve Nav2 overlay hooks only; do not over-customize Phase 1 around Nav2 internals

### slam_toolbox

- likely entry surface:
  - top-level `package.xml`, `launch/`, `config/`, `src/`
- useful interface takeaways:
  - ROS package structure
  - map lifecycle and service patterns
- AgentSlam use:
  - use as ROS packaging and map-tooling reference, not as a Phase 1 blocker

### vision_opencv

- likely entry surface:
  - `cv_bridge`
  - `image_geometry`
- useful interface takeaways:
  - ROS image conversion boundaries
  - camera model utilities
- AgentSlam use:
  - align camera and image handling conventions with stock ROS packages

### OneMap

- likely entry surface:
  - `mapping/`, `planning/`, `config/`, top-level evaluation scripts
- useful interface takeaways:
  - semantic map organization ideas
  - map/planning separation
- AgentSlam use:
  - mine semantic map structuring ideas for Phase 2 without copying runtime assumptions

### concept-graphs

- likely entry surface:
  - `conceptgraph/`, `setup.py`, streamlined detection README
- useful interface takeaways:
  - graph-oriented semantic abstractions
- AgentSlam use:
  - later semantic enrichment reference, not Phase 1 runtime dependency

### MASt3R-SLAM

- likely entry surface:
  - `main.py`, `mast3r_slam/`, `config/`
- useful interface takeaways:
  - entrypoint structure for a heavier visual SLAM stack
- AgentSlam use:
  - deferred localization research only

### GitNexus

- likely entry surface:
  - CLI commands `analyze`, `status`, `query`, `context`, `impact`
- useful interface takeaways:
  - local indexing workflow is practical and can be scripted
- AgentSlam use:
  - primary code-understanding tool for the main repo and cloned refs

## Failed Clone Notes

- `IsaacSim-ros_workspaces`
  - high priority because it would sharpen real bridge and launch patterns
- `message_filters`
  - important for exact synchronization guidance, but not blocking the offline Phase 1 baseline
- `HOV-SG`
  - semantic graph reference deferred by environment transport failures
- `DROID-SLAM`
  - deferred localization reference and not part of the current mainline
