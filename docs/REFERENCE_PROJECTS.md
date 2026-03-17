# Reference Projects

## Role Categories

### Interface And Bring-Up References

- `IsaacSim-ros_workspaces`
  - primary reference for bridge structure, launch surfaces, and ROS workspace patterns
- `navigation2`
  - primary reference for later Nav2 overlay boundaries and goal execution integration
- `vision_opencv`
  - primary reference for image handling and OpenCV bridge conventions
- `message_filters`
  - primary reference for synchronization patterns in visual plus IMU flows

### Mapping And Semantic Design References

- `slam_toolbox`
  - useful for ROS map lifecycle patterns, but not the Phase 1 semantic mapping core
- `OneMap`
  - useful for semantic map structuring ideas
- `HOV-SG`
  - useful for scene graph relationship modeling
- `concept-graphs`
  - useful for later semantic grounding and graph abstractions

### Deferred Algorithm References

- `DROID-SLAM`
  - future localization research, not Phase 1 critical path
- `MASt3R-SLAM`
  - future localization research, not Phase 1 critical path

### Tooling Reference

- `GitNexus`
  - main code-understanding and impact-analysis tool for local and upstream repositories

## Borrow Strategy

- borrow interfaces, launch patterns, and adapter ideas before borrowing implementation
- do not deep-bind the AgentSlam runtime to any upstream repo until the Phase 1 contract is stable
- treat `refs/` as analysis material first and integration material second

## What To Avoid Copying Blindly

- heavyweight SLAM or scene-graph pipelines that assume a much larger runtime footprint
- LiDAR-first bring-up patterns that conflict with the visual plus IMU baseline
- repo-specific custom messages unless they solve a proven AgentSlam problem
