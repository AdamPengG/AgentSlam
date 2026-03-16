# AgentSlam Project Context

## Goal

AgentSlam is being prepared as an integration-first semantic localization and navigation project. The immediate objective is to finish Phase 0 bootstrap work so the repository, documentation, validation flow, and future ROS 2 workspace structure are ready before algorithm development begins.

## Fixed Context

- Project root: `/home/peng/AgentSlam`
- GitHub remote: `https://github.com/AdamPengG/AgentSlam.git`
- Isaac Sim asset root: `/home/peng/isaacsim_assets`
- Preferred simulation scene: office
- Preferred robot: Nova wheeled robot
- Sensor constraint: visual plus IMU only
- References directory: `/home/peng/AgentSlam/refs`

## Current Working Assumptions

- Phase 0 focuses on repository setup, project configuration, documentation, reports, and workspace skeletons.
- Early runtime integration should start from GT pose rather than a learned or SLAM-based localization replacement.
- Standard ROS 2 messages should be preferred until a custom message is proven necessary.
- `refs/` will remain a local, ignored staging area for upstream repositories rather than part of the main repository history.

## Isaac Discovery Snapshot

Prompt 1 did not assume an Isaac Sim executable path. A basic local search found:

- asset root present at `/home/peng/isaacsim_assets`
- candidate install directory present at `/home/peng/IsaacSim`
- no `isaacsim`, `isaac-sim.sh`, or `omniverse-launcher` command available on `PATH` during this run

The install path is therefore still treated as unconfirmed. Prompt 2 should formalize discovery with a repeatable script and capture exact launch candidates.

## Reference Repository Plan

Planned upstreams will be cloned under `refs/` in a later prompt. The initial integration direction expects references for:

- Isaac Sim ROS workspaces and bridge patterns
- Nav2 and ROS 2 message contracts
- semantic mapping and scene-graph systems
- visual SLAM backends that can inform later localization upgrades

## Open Questions

- Which exact Isaac Sim launcher and Python entrypoints are valid on this machine
- Which office USD assets and Nova robot assets are directly reusable from the local asset root
- Which upstream repository should anchor the first semantic map representation
- How much of navigation should stay within stock Nav2 versus a project-specific overlay
