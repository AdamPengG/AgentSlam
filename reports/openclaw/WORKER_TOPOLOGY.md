# OpenClaw Worker Topology

## Planned agents

### planner

- workspace: `~/.openclaw/workspaces/agentslam/planner`
- role: planning, docs, blockers, next-step selection

### coder

- workspace: `~/.openclaw/workspaces/agentslam/coder`
- role: code changes through Codex

### evaluator

- workspace: `~/.openclaw/workspaces/agentslam/evaluator`
- role: build, smoke, fixture, replay, validation

### reporter

- workspace: `~/.openclaw/workspaces/agentslam/reporter`
- role: summaries, handoff, operator notifications, gate state

## Isolation policy

- distinct workspaces
- distinct `agentDir` values
- shared repo root only through controlled wrapper scripts
- no browser, canvas, or node tools in the planned baseline
