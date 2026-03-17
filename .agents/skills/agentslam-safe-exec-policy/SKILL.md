# agentslam-safe-exec-policy

Use whenever agent behavior might drift into broad or unsafe shell usage.

## Hard rules

- prefer `ops/openclaw/bin/agentslam_*.sh`
- do not scan the whole home directory
- never write to `refs/`, `GS4`, `IsaacSim`, or `isaacsim_assets`
- keep OpenClaw as the control plane and Codex as the code executor
- use reports for durable state, not ad hoc terminal-only conclusions

## Escalate when

- a task needs new external permissions
- a read-only reference tree appears to need edits
- a deployment change would replace a currently working live config
