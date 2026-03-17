# agentslam-orchestrator

Shared OpenClaw skill mirror.

- Read `reports/openclaw/CURRENT_STATE.md` first when it exists.
- Route work through `plan -> implement -> test -> report -> gate`.
- Prefer `ops/openclaw/bin/agentslam_*.sh` entrypoints.
- Use the smallest sufficient model and context for the current step.
- Only escalate to heavy coding or replay work when the task truly needs it.
- Stop on `awaiting_user_review`.
