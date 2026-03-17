# OpenClaw Path Contract

## Writable

- `/home/peng/AgentSlam`
- `~/.openclaw`
- `~/.codex`
- repo-created worktree, cache, temp, report, and artifact paths

## Read-only references

- `/home/peng/GS4`
- `/home/peng/IsaacSim`
- `/home/peng/isaacsim_assets`
- `/home/peng/AgentSlam/refs/*`

## Control-plane paths

- repo source root: `/home/peng/AgentSlam/ops/openclaw`
- live OpenClaw home: `~/.openclaw`
- live skills sync target: `~/.openclaw/skills`
- planned agent workspaces:
  - `~/.openclaw/workspaces/agentslam/planner`
  - `~/.openclaw/workspaces/agentslam/coder`
  - `~/.openclaw/workspaces/agentslam/evaluator`
  - `~/.openclaw/workspaces/agentslam/reporter`

## Guardrails

- Do not let OpenClaw or Codex scan the whole home directory by default.
- Keep filesystem tools workspace-scoped wherever practical.
- Never write into `/home/peng/GS4`, `/home/peng/IsaacSim`,
  `/home/peng/isaacsim_assets`, or `refs/`.
