# Adapter Decisions

## Current Decisions

### Bridge Layer

- use locally documented launcher and asset candidates first
- treat `IsaacSim-ros_workspaces` as a desired reference, but do not block Phase 1 on its absence
- keep Phase 0 bridge outputs aligned with standard ROS messages

### Mapping Layer

- choose a minimal object-centroid semantic map for Phase 1
- defer room graph richness to a later phase
- keep the fixture path independent of simulator bring-up

### Query Layer

- use JSON export plus a simple label-query CLI for Phase 1
- postpone service-heavy query APIs until the map format is more stable

### Navigation Layer

- reserve Nav2 overlay boundaries now
- do not bind Phase 1 semantic mapping to a full navigation runtime

### Localization Layer

- keep GT pose as the authoritative localization input for this phase
- treat DROID-SLAM and MASt3R-SLAM as later research tracks only

## Explicit Non-Decisions

- no custom semantic ROS message set yet
- no LiDAR-first bridge path
- no deep code copy from upstream mapping or SLAM repos
