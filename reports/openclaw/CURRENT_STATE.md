# AgentSlam OpenClaw Current State

## One-Screen Summary

- Mission: OpenClaw is the AgentSlam control plane; Codex is the coding and
  evaluation engine.
- Project repo: `/home/peng/AgentSlam`
- OpenClaw workspace: `/home/peng/.openclaw/workspace`
- OpenClaw gateway: live on this machine
- Codex auth: available locally through ChatGPT login

## Engineering Status

- Phase 1 replay-backed semantic mapping is reviewable.
- Codex nightly build, test, replay, summary, and handoff flow is locally
  runnable.
- OpenClaw skills for AgentSlam are synced to `~/.openclaw/skills`.
- OpenClaw live config is deployed in low-token, conservative 7x24 mode.

## Current Priorities

1. keep OpenClaw stable and low-noise
2. preserve Phase 1 regression evidence
3. keep nightly and triage paths healthy
4. defer heavy live Isaac work until control-plane behavior is stable

## Token-Efficiency Rules

- planner and reporter use lighter models by default
- coder and evaluator keep the heavier model for real implementation and
  verification
- read this file before opening larger docs
- prefer wrapper scripts and shell summaries over feeding raw logs to the model
- keep concurrency low
- do not wake models on a schedule unless something changed or a real job is
  due
- session reset and cron retention are intentionally shorter than before

## Escalate To Heavy Work Only When Needed

- code changes under `ros_ws/src/`
- test or build failures that need real debugging
- replay or nightly evaluation
- operator-requested deep review

## Key Reports

- OpenClaw status: `reports/openclaw/WORKSPACE_BOOTSTRAP_STATUS.md`
- runtime facts: `reports/openclaw/RUNTIME_MODE.md`
- blockers: `reports/SETUP_BLOCKERS.md`
- latest nightly: `reports/nightly/latest_summary.md`
