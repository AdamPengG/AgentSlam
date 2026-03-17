# Prompt 5 Starting State

## Short Status Summary

AgentSlam starts Prompt 5 from a good Phase 1 baseline but without a durable 24x7 operations layer. The repo can already build and validate the replay-backed semantic mapping path locally, yet it does not have `codex exec` wrappers, workflow serialization, runner setup guides, repo-local ops skills, or GitHub workflow scaffolding for continuous use.

## What Already Works

- local Phase 1 fixture regression:
  - `bash scripts/run_phase1_fixture.sh`
- focused unit tests for semantic mapper and fixture IO
- replay-backed bridge smoke:
  - `bash scripts/run_phase0_bridge_smoke.sh`
- replay demo and operator demo:
  - `bash scripts/run_phase1_replay_demo.sh`
  - `bash scripts/run_phase1_office_demo.sh`
- package-level ROS workspace build:
  - `colcon build --packages-select sim_bridge_pkg semantic_mapper_pkg room_graph_pkg semantic_query_pkg nav2_overlay_pkg localization_adapter_pkg eval_tools_pkg`
- local GitNexus index is present and up to date
- local Codex CLI is installed and `codex login status` reports ChatGPT-managed login

## What Exists Only As Documentation Or Interactive Practice

- Codex Cloud and GitHub integration flow
- GitHub PR review and `@codex` operational guidance
- self-hosted runner onboarding
- serialized non-interactive `codex exec` automation
- repo-local skill conventions for nightly validation and triage

## What Is Still Demo-Oriented

- the accepted runtime path is replay-backed, not a live Isaac ROS bridge
- multi-agent use is prepared in config but not proven as the 24x7 scheduler
- no workflow currently turns the existing scripts into scheduled or dispatchable operations

## Current Blockers And Gaps

- Cloud and GitHub integration still require manual activation outside the repo
- no self-hosted runner is registered yet from the repo side
- no lock wrapper currently protects ChatGPT-managed auth from concurrent `codex exec` jobs
- live Isaac ROS topic publishing is still outside the Phase 1 acceptance path
- ROS runtime still depends on system Python rather than the active conda interpreter

## Chosen Prompt 5 Architecture

- Codex Cloud plus GitHub integration for review and background task entry
- trusted Linux self-hosted runner plus `codex exec` for build, test, nightly validation, plan refresh, and triage
- repo-local skills plus `AGENTS.md` for repeatable operational behavior
- GitHub Actions for scheduling and dispatch

## Why The Current Prompt Avoids API Keys

- the operator already has a workable ChatGPT-managed Codex login on this machine
- Prompt 5 explicitly asks for a Codex-only path
- the repo goal is sustained engineering automation, not embedding OpenAI API calls into project code

## Why Agents SDK Is Deferred

- the missing value is orchestration and operator hygiene, not another runtime framework
- this phase can get durable wins from prompts, shell wrappers, and workflows without introducing a new dependency surface

## This Prompt's In-Repo Deliverables

- ops architecture docs and runbooks
- an `ops_dev` role
- repo-local skills under `.agents/skills/`
- prompt templates under `prompts/exec/`
- scripts under `scripts/ops/`
- workflow YAML under `.github/workflows/`
- validation and handoff reports

## Manual Activation Items

- connect Codex Cloud to GitHub
- enable review and automatic review features in the product UI
- register and label a self-hosted runner
- complete `codex login` or `codex login --device-auth` on the runner if needed
