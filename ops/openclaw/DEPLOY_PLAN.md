# OpenClaw Deploy Plan

## Phase A: Baseline capture

- inventory the live `~/.openclaw` layout
- capture security audit and channel status
- capture Codex and GitNexus readiness

## Phase B: Repo-side source

- write split config fragments under `ops/openclaw/src/conf.d/`
- define shared skills and state templates
- add shell entrypoints under `ops/openclaw/bin/`

## Phase C: Dry-run deployment

- render a flat config into a temporary home
- run `openclaw config validate`
- record outputs in `reports/openclaw/DEPLOY_STATUS.md`

## Phase D: Controlled live deployment

- back up the live config into `~/.openclaw/backups/<timestamp>/`
- write the rendered config
- sync shared skills
- restart the user service
- run status and security checks

## Phase E: Go-live gating

- keep cron disabled until:
  - Telegram DM path is confirmed
  - browser and canvas are disabled
  - `plugins.allow` is pinned
  - agent workspaces and wrapper scripts are in place
