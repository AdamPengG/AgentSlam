# AgentSlam OpenClaw Control Plane

This directory is the versioned source of truth for the AgentSlam OpenClaw
control plane.

## Layout

- `src/conf.d/`: strict JSON-in-JSON5-extension config fragments
- `src/openclaw.json5`: repo-side include manifest for humans
- `src/shared-skills/`: OpenClaw-shared skills to sync into `~/.openclaw/skills`
- `bin/`: render, deploy, validate, status, and wrapper entrypoints
- `state/`: example state-machine files for phase and completion gating

## Operating model

- We keep repo-side config split into fragments for reviewability.
- We do not hand-edit `~/.openclaw/openclaw.json`.
- `bin/render_openclaw.sh` flattens fragments into one runtime config because
  the current local OpenClaw install does not expose a documented runtime
  include mechanism.
- `bin/deploy_openclaw.sh` backs up the live OpenClaw config before writing.
- `bin/validate_openclaw.sh` renders into a temporary home and runs
  `openclaw config validate`.

## First target

Phase 0 for this workstream is not SLAM code. It is:

1. secure the local OpenClaw baseline
2. make OpenClaw repo-managed and recoverable
3. route controlled work into Codex through wrapper scripts
4. only then turn on durable cron-driven automation
