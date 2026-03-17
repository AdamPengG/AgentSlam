# AgentSlam Architecture Overview

## System Intent

AgentSlam is being advanced in staged slices. The current mainline is not “full autonomy,” but a verifiable Phase 1 semantic mapping baseline that uses:

- GT pose for localization
- visual plus IMU sensing
- offline-first fixture or replay validation
- standard ROS 2 contracts where practical

## Current System Shape

```text
Isaac Sim / Offline Fixture
        |
        v
sim_bridge_pkg + ros_ws/launch + ros_ws/config
        |
        v
RGB / depth / camera_info / IMU / GT pose / TF / clock
        |
        v
semantic_mapper_pkg
        |
        +--> semantic map export
        +--> query CLI / query package hooks
        +--> room graph placeholders
        |
        v
nav2_overlay_pkg (deferred integration hooks)
```

## Package Boundaries

- `sim_bridge_pkg`
  - owns bridge-facing conventions, launcher choices, and Phase 0 bring-up placeholders
- `semantic_mapper_pkg`
  - owns Phase 1 core logic: projection, fusion, export, and minimal query flow
- `room_graph_pkg`
  - reserves the room-graph boundary for Phase 2 without pulling it into the Phase 1 critical path
- `semantic_query_pkg`
  - reserves richer runtime query surfaces while Phase 1 uses a simple offline query CLI
- `nav2_overlay_pkg`
  - keeps navigation hooks ready without stealing focus from semantic mapping
- `localization_adapter_pkg`
  - protects the GT-pose-first contract and future localization replacement boundary
- `eval_tools_pkg`
  - holds evaluation and fixture-runner responsibilities as they stabilize

## Phase Boundaries

### Phase 0

- repository, scripts, docs, clone strategy, and bridge contracts
- no heavy runtime dependency on a full Isaac GUI bring-up

### Phase 1

- GT-pose-driven semantic mapping baseline
- offline fixture path required
- export and query path required
- at least one automated test required

### Later Phases

- room graph growth
- semantic navigation overlay
- localization replacement
- heavier scene graph or SLAM integration

## Why GT Pose Plus Visual And IMU Is The Mainline

- it avoids blocking semantic mapping on unfinished SLAM replacement work
- it keeps interfaces closer to the data AgentSlam actually needs
- it makes fixture and replay validation practical early
- it prevents LiDAR-first assumptions from dictating the architecture too early
