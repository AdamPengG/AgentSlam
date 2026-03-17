# Upstream Research Plan

## Goal

Prompt 3 should clone only the repositories that are already justified by an integration plan. This document defines what each upstream is expected to answer before AgentSlam starts implementation-heavy work.

## GitNexus Suggested Analysis Order

1. AgentSlam local repository
   - reason: establish local docs, scripts, and intended contract surfaces before reading upstreams
2. `IsaacSim-ros_workspaces`
   - reason: bridge and launch structure is the first hard dependency
3. `navigation2`
   - reason: initial navigation overlay should stay close to stock Nav2 boundaries
4. `vision_opencv`
   - reason: image conversion and transport conventions affect early bridge design
5. `message_filters`
   - reason: time synchronization is central for image plus IMU plus GT pose
6. `GitNexus`
   - reason: maintain a reliable indexing workflow for the main repo and refs
7. `slam_toolbox`
   - reason: baseline ROS SLAM comparison and map tooling references
8. `OneMap`
   - reason: semantic map structure ideas for Phase 2
9. `HOV-SG`
   - reason: scene graph patterns for richer semantics
10. `concept-graphs`
    - reason: graph grounding and semantic abstraction references
11. `DROID-SLAM`
    - reason: deferred localization-upgrade research
12. `MASt3R-SLAM`
    - reason: deferred localization-upgrade research

## Repository-By-Repository Questions

### IsaacSim-ros_workspaces

- inspect: workspace layout, launch entrypoints, bridge nodes, topic naming, TF conventions, package dependencies
- integration target: bridge_dev and setup_dev
- main risk: version mismatch between local Isaac install and upstream samples

### navigation2

- inspect: bring-up structure, behavior tree extension points, costmap plugins, parameter patterns
- integration target: nav_dev
- main risk: over-customizing before the baseline bridge is stable

### slam_toolbox

- inspect: launch flows, map persistence patterns, message contracts, optional integration seams
- integration target: mapping_dev
- main risk: pulling 2D SLAM assumptions into a GT-pose-first semantic workflow too early

### vision_opencv

- inspect: image transport and `cv_bridge` conventions relevant to ROS 2 image ingestion
- integration target: bridge_dev and mapping_dev
- main risk: unnecessary wrapper code if stock message handling is enough

### message_filters

- inspect: synchronization primitives and recommended ROS 2 patterns
- integration target: bridge_dev and mapping_dev
- main risk: mismatched timestamps or hidden queueing behavior in the visual plus IMU pipeline

### OneMap

- inspect: semantic map abstractions, room or object graph structures, storage patterns, adapter seams
- integration target: mapping_dev
- main risk: semantic model complexity outrunning Phase 1 needs

### HOV-SG

- inspect: scene graph abstractions, relationship modeling, likely dependencies
- integration target: mapping_dev
- main risk: heavy offline assumptions or dataset coupling

### concept-graphs

- inspect: graph construction and semantic grounding surfaces
- integration target: mapping_dev
- main risk: research-code assumptions not suitable for online integration

### DROID-SLAM

- inspect: entrypoints, sensor assumptions, GPU and dependency load, possible offline use
- integration target: later localization research
- main risk: heavy dependency footprint and runtime cost

### MASt3R-SLAM

- inspect: entrypoints, training or inference assumptions, dependency stack, online versus offline suitability
- integration target: later localization research
- main risk: high complexity relative to GT-pose-first milestones

### GitNexus

- inspect: analyze, query, context, and impact workflows plus index storage expectations
- integration target: repo_researcher and tester
- main risk: indexing friction or environment-specific setup details

## Phase Priority Split

### Phase 0 And Early Phase 1

- `IsaacSim-ros_workspaces`
- `navigation2`
- `vision_opencv`
- `message_filters`
- `GitNexus`

### Phase 1 To Phase 2

- `slam_toolbox`
- `OneMap`
- `HOV-SG`
- `concept-graphs`

### Deferred Until After GT-Pose-First Validation

- `DROID-SLAM`
- `MASt3R-SLAM`

## Research Output Expectations

Each upstream analysis file produced in Prompt 3 should capture:

- entry files and launch surfaces
- key modules or packages
- expected inputs and outputs
- likely AgentSlam adapter locations
- dependency and install risks
- whether the repo is best suited for online runtime, offline tooling, or later enhancement
