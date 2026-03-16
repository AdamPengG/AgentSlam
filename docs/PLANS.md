# AgentSlam Development Plan

## Phase 0: Bootstrap and Readiness

Objective: make the repository operational before business logic lands.

Current scope:

- initialize git, remote, ignore rules, and project-level Codex configuration
- establish multi-agent role definitions
- create project skeleton directories and documentation seeds
- record Git status, Isaac discovery results, and setup blockers
- prepare the workspace for later script generation, environment audit, and upstream analysis

Exit criteria:

- required bootstrap files exist
- repository is on `main` with `origin` configured
- initial docs cover goals, interfaces, dataflow, evaluation, and unresolved items
- setup status and blockers are documented

## Phase 1: Simulation-to-ROS Baseline

Objective: bring up a minimal office-scene runtime using standard ROS 2 contracts.

Planned work:

- discover and confirm Isaac Sim launcher, Python, and asset entrypoints
- define the first launch structure under `ros_ws/launch`
- wire camera, camera info, IMU, `/clock`, `/tf`, and GT pose topics
- keep the robot baseline on a Nova wheeled platform
- avoid LiDAR-dependent defaults

Exit criteria:

- simulation can publish the agreed visual and IMU topics
- TF and time contracts are documented and reproducible
- a smoke checklist covers startup, topic checks, and static validation

## Phase 2: Semantic Mapping Skeleton

Objective: stand up the minimum semantic world model needed for room-aware navigation.

Planned work:

- define room graph and semantic map abstractions
- connect visual observations to semantic entities
- draft a query interface for room lookup, semantic labels, and route hints

## Phase 3: Navigation Overlay

Objective: add room-aware navigation behaviors on top of standard Nav2 components.

Planned work:

- route graph and room-to-room planning overlay
- behavior tree hooks for semantic goals
- costmap filter or semantic constraint integration where needed

## Deferred Work

- replacing GT pose with learned or SLAM-based localization
- large-scale upstream dependency installation
- full algorithmic integration of semantic SLAM backends
