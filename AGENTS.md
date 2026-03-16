# AgentSlam Working Rules

## Scope

This repository is an integration workspace for AgentSlam. Phase 0 is reserved for infrastructure, workspace scaffolding, documentation, and validation setup. Do not rush into full algorithm implementation.

## Repository Boundaries

- `refs/` contains upstream reference repositories and is read-only from the perspective of this repo.
- Do not make business changes inside `refs/`, and do not include `refs/` in main-repo commits.
- Treat `/home/peng/AgentSlam` as the project root for all scripts, reports, and generated documentation.

## Technical Direction

- Start with GT pose as the localization source; replacing localization belongs to a later phase.
- The default sensing stack is visual plus IMU only. Do not enable LiDAR by default.
- Favor standard ROS 2 messages and established packages early. Introduce custom messages only when the integration benefit is clear and documented.
- Isaac office scenes and a Nova wheeled robot are the preferred simulation baseline until a change is explicitly approved.

## Documentation Contracts

- Any important interface change must update `docs/INTERFACES.md` and `docs/DATAFLOW.md` in the same workstream.
- Planning or evaluation changes must keep `docs/PLANS.md` and `docs/EVAL.md` aligned with current assumptions.
- Record environment blockers and unresolved setup gaps in `reports/SETUP_BLOCKERS.md`.

## Verification Gates

- Any mergeable change must pass at least one build, one smoke check, and one replay or static validation pass.
- Keep verification evidence in `reports/` instead of only printing terminal output.
- Scripts should be repeatable, conservative, and safe to rerun.

## Multi-Agent Coordination

- Only one write-heavy agent may make large edits under `ros_ws/src` at a time.
- Planning and research roles should prefer documentation outputs over code edits.
- Bridge, mapping, navigation, and test work should converge through documented interfaces instead of private assumptions.

## Git Hygiene

- Do not guess `git user.name` or `git user.email`; if either is missing, stop before commit or push and write a setup report.
- Do not push unless explicitly requested.
