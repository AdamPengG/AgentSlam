---
name: isaac-office-nova-audit
description: Use this skill when you need to audit the local Isaac Sim install, Office scene assets, and Nova wheeled robot baseline for AgentSlam.
---

# Isaac Office Nova Audit

## Trigger

Use this skill when:

- validating whether the local machine still has the preferred Isaac release entrypoints
- checking Office scene and Nova Carter asset availability
- writing setup, runner, or operator documentation that depends on those local paths

## Do Not Trigger

Do not use this skill when:

- the task is only about Codex Cloud, GitHub review, or workflow YAML
- the task only needs fixture validation and never touches Isaac assumptions
- the task is about algorithm changes inside `ros_ws/src`

## Inputs

- expected Isaac root: `/home/peng/IsaacSim`
- expected asset root: `/home/peng/isaacsim_assets`
- discovery helpers:
  - `scripts/discover_isaac_assets.sh`
  - `scripts/run_isaac_office_nova.sh --validate-only`
- blocker tracker: `reports/SETUP_BLOCKERS.md`

## Outputs

- confirmed launcher and Python entrypoint paths
- confirmed Office scene and Nova USD candidate paths
- explicit fallback or blocker notes if any preferred path is missing

## Workflow

1. Read the latest `reports/ISAAC_DISCOVERY.md` and `reports/SETUP_BLOCKERS.md`.
2. Prefer existing discovery scripts over ad hoc file searching.
3. Confirm the release entrypoints and asset paths still match the Phase 1 contract.
4. If a preferred path is missing, record the exact missing path and fallback options.
5. Keep conclusions grounded in observed local filesystem state.

## Notes

- This skill is an audit skill, not a live GUI bring-up recipe.
- If the audit reveals a new blocker, update `reports/SETUP_BLOCKERS.md`.
