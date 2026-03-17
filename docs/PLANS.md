# AgentSlam Development Plan

## Hard Constraints

- project root stays at `/home/peng/AgentSlam`
- preferred simulation scene is an office environment
- preferred robot baseline is a Nova wheeled robot when a suitable local asset is confirmed
- sensing scope for the first executable slice is visual plus IMU only
- LiDAR is explicitly out of scope by default for Phase 0 and the initial Phase 1 slice
- GT pose is the initial localization source; VSLAM replacement should happen behind `/agentslam/localization/odom` without changing mapper contracts

## Phase 0: Development Readiness

Objective: make the repository ready for upstream cloning, local environment checks, and disciplined multi-agent work without starting full algorithm implementation.

Minimum executable tasks:

1. keep bootstrap files, reports, and scripts in a runnable state
2. audit local shell dependencies and Isaac candidate resources
3. define the first interface and dataflow contract for visual plus IMU work
4. prepare validation checklists for smoke, acceptance, clone, and development readiness
5. produce an upstream research plan before cloning reference repositories

### Phase 0 Task Split

#### pm

- refine planning, interface, dataflow, and evaluation docs
- keep the visual plus IMU and no-LiDAR constraint explicit
- break Prompt 3 and Prompt 4 work into bridge, mapping, and navigation handoff units

#### setup_dev

- maintain `scripts/clone_refs.sh`
- maintain `scripts/discover_isaac_assets.sh`
- maintain `scripts/env_audit.sh`
- record environment and Isaac discovery outputs in `reports/`

#### tester

- validate bootstrap file presence and configuration completeness
- maintain smoke and acceptance checklists
- convert project assumptions into pass/fail gates before upstream integration starts

Exit criteria:

- Prompt 1 bootstrap files remain valid
- Prompt 2 scripts exist and are executable
- `reports/ENV_AUDIT.md` and `reports/ISAAC_DISCOVERY.md` are current
- upstream research planning documents exist
- validation checklists exist for Prompt 3 and later bring-up

## Phase 1: First Executable Simulation Slice

Objective: stand up the smallest reproducible simulation-to-ROS path for office navigation research using camera, camera info, IMU, and GT pose first, while reserving TF and `/clock` for the live bridge follow-up.

### Phase 1 Task Split

#### bridge_dev

- confirm the preferred Isaac launcher and Python entrypoint from discovered candidates
- choose an office scene entry and a local Nova robot candidate, falling back to another wheeled robot only if necessary
- define launch structure for `/clock`, `/tf`, `/tf_static`, image, camera info, IMU, and GT pose
- freeze initial topic names and frame assumptions in docs before heavier code work

#### mapping_dev

- define a semantic map skeleton that consumes image, camera info, IMU, and GT pose
- prefer file-backed or lightweight in-memory artifacts before ROS-heavy custom interfaces
- prepare room graph and semantic query placeholders rather than full mapping logic

#### nav_dev

- prepare a Nav2-compatible overlay plan that consumes GT pose and future semantic outputs
- define route graph and semantic-goal placeholders
- keep LiDAR-dependent plugins and assumptions disabled by default

Exit criteria:

- the bridge contract is documented and smoke-testable
- a minimal office plus Nova candidate path exists on disk
- mapping and navigation skeletons can consume the agreed interfaces without custom message debt
- tester checklists are sufficient to validate a first launch attempt

### Phase 1 Closure Status

- Isaac release launcher and Python pair: validated
- Office + Nova Carter asset pair: validated
- offline fixture path: validated
- ROS replay path into the mapper: validated
- top-level operator demo script: validated
- live Isaac ROS bridge: deferred to the next step

### Phase 1 Current Implementation Snapshot

- `semantic_mapper_pkg` supports `fixture`, `bag_replay`, and `live_isaac` modes
- `sim_bridge_pkg` publishes a replay-friendly standard-topic stream from JSON fixtures
- `localization_adapter_pkg` now normalizes localization output onto `/agentslam/localization/odom` with GT fallback and future VSLAM headroom
- `ros_ws/launch/phase1_vslam_stereo.launch.py` now defines the preferred stereo VSLAM bring-up path for the current GS4-hosted Isaac ROS backend
- the baseline exports JSON semantic objects and label query outputs
- `nav2_overlay_pkg.localized_mapping` now exports a lightweight 2D occupancy-style grid from localized observations
- the exported-map query path now supports spatial filtering without adding a live service layer
- `nav2_overlay_pkg` now includes an offline exploration scaffold that grows the semantic map from multiple candidate viewpoints
- build, unit tests, bridge smoke, replay demo, localized mapping demo, and office demo validation have been executed
- the offline exploration demo has been built, unit-tested, and artifact-validated
- a real `isaac_ros_visual_slam` bring-up path now exists through an external overlay and a stereo-aligned launch contract
- full end-to-end VSLAM validation now depends on a live front-stereo Isaac or GS4 producer on this host

## Prompt 5: 24x7 Ops Enablement

Objective: package the validated Phase 1 baseline into a Codex-only operations layer that supports scheduled regression, bounded triage, and owner-facing handoff without introducing API keys or new agent runtimes.

Planned work:

- add an `ops_dev` role for workflows, runner docs, prompts, and automation scripts
- create repo-local skills for stable acceptance and triage workflows
- add `codex exec` wrappers with auth checks and locking
- add self-hosted-runner-oriented GitHub workflows for CI, nightly eval, plan refresh, and triage
- keep Cloud activation and GitHub review enablement as documented manual steps rather than prompt blockers

Exit criteria:

- at least one local locked `codex exec` run is validated
- at least one repeatable Phase 1 suite script writes report and artifact outputs for nightly use
- workflows exist for CI, nightly eval, plan refresh, and triage
- operator-facing docs exist for Cloud setup, runner setup, auth, and day-to-day operations

## OpenClaw Control Plane Bootstrap

Objective: add a repo-managed OpenClaw control plane that can safely orchestrate Codex work without replacing the existing Prompt 5 runner scaffold.

Planned work:

- create `ops/openclaw/` as the versioned source of truth
- keep live deployment backup-first and dry-run-first
- pin a stricter security baseline than the current live OpenClaw config
- add AgentSlam-specific OpenClaw skills and wrapper scripts
- keep cron conservative and disabled until the new config validates cleanly

Exit criteria:

- repo-side config fragments and deployment scripts exist
- baseline reports under `reports/openclaw/` capture current live risks
- validation succeeds in a temporary home
- the live cutover checklist is explicit before any real replacement of `~/.openclaw`

## Phase 2: Semantic Mapping Expansion

Objective: move from placeholders to a usable semantic room graph and map query layer.

Planned work:

- integrate room-aware semantic state
- define persistence format for semantic and room artifacts
- decide whether online updates, offline post-processing, or a hybrid approach is the default

## Phase 3: Navigation Overlay Expansion

Objective: attach room-aware planning and behavior-tree control to the validated bridge and mapping contracts.

Planned work:

- upgrade the offline exploration scaffold into a route graph and live exploration loop
- semantic goal interpretation
- Nav2 behavior tree hooks and costmap filter integration as needed

## Deferred Work

- learned or SLAM-based localization replacing GT pose
- dense geometric mapping through `isaac_ros_nvblox` or an equivalent production backend
- large dependency installs beyond what Prompt 3 and Prompt 4 require
- full integration of DROID-SLAM or MASt3R-SLAM into the runtime loop
