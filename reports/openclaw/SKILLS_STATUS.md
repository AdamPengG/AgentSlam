# OpenClaw Skills Status

## Repo-local skills created

- `agentslam-orchestrator`
- `agentslam-phase0-isaac-bridge`
- `agentslam-phase1-gt-semantic-map`
- `agentslam-onemaplike-roadmap`
- `agentslam-nightly-eval`
- `agentslam-blocker-triage`
- `agentslam-safe-exec-policy`
- `agentslam-telegram-notify`

## Shared OpenClaw skills created

The same skill family now exists under:

- `ops/openclaw/src/shared-skills/`

## Deployment model

- repo-local skills support Codex work in this repo
- shared skills are the source of truth for OpenClaw-side reusable behavior
- live sync target: `~/.openclaw/skills`

## Live sync state

Shared AgentSlam skills are now present under:

- `~/.openclaw/skills/agentslam-orchestrator`
- `~/.openclaw/skills/agentslam-phase0-isaac-bridge`
- `~/.openclaw/skills/agentslam-phase1-gt-semantic-map`
- `~/.openclaw/skills/agentslam-onemaplike-roadmap`
- `~/.openclaw/skills/agentslam-nightly-eval`
- `~/.openclaw/skills/agentslam-blocker-triage`
- `~/.openclaw/skills/agentslam-safe-exec-policy`
- `~/.openclaw/skills/agentslam-telegram-notify`

This means the live OpenClaw home now has a reusable AgentSlam-specific skill
baseline in addition to the repo-local skills.
