# Expected Upstreams

## Prompt 3 Clone Targets

- `IsaacSim-ros_workspaces`
  - purpose: reference ROS workspace layout, Isaac bridge examples, launch and integration patterns
  - priority: Phase 0 and early Phase 1
- `navigation2`
  - purpose: Nav2 overlay boundaries, goal execution, behavior trees, and navigation configs
  - priority: Phase 0 and early Phase 1
- `slam_toolbox`
  - purpose: baseline ROS SLAM patterns and map tooling reference
  - priority: Phase 1 and later comparison work
- `vision_opencv`
  - purpose: OpenCV bridge and image handling conventions for ROS 2
  - priority: Phase 0 and early Phase 1
- `message_filters`
  - purpose: synchronization patterns for image, camera info, IMU, and GT pose
  - priority: Phase 0 and early Phase 1
- `OneMap`
  - purpose: semantic mapping and scene-centric map structuring ideas
  - priority: Phase 1 and Phase 2
- `HOV-SG`
  - purpose: higher-order scene graph references for semantic relationships
  - priority: Phase 2
- `concept-graphs`
  - purpose: semantic graph and grounding ideas for later integration
  - priority: Phase 2
- `DROID-SLAM`
  - purpose: later-stage visual SLAM or localization upgrade research
  - priority: deferred until after GT-pose-first validation
- `MASt3R-SLAM`
  - purpose: later-stage visual SLAM or localization upgrade research
  - priority: deferred until after GT-pose-first validation
- `GitNexus`
  - purpose: repository indexing and code-understanding support during upstream analysis
  - priority: Phase 0 and Prompt 3 infrastructure

## Clone Notes

- `DROID-SLAM` and `MASt3R-SLAM` should be cloned with submodule support
- all upstreams live under `refs/` and remain read-only from the perspective of AgentSlam
- `refs/` stays ignored by the main repository
