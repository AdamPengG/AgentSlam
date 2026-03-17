# OpenClaw Deploy Status

## Repo-side source created

- `ops/openclaw/src/conf.d/*.json5`
- `ops/openclaw/src/openclaw.json5`
- `ops/openclaw/bin/render_openclaw.sh`
- `ops/openclaw/bin/deploy_openclaw.sh`
- `ops/openclaw/bin/validate_openclaw.sh`

## Live deployment state

- live `~/.openclaw` was audited
- repo-side validation passed in a temporary home
- dry-run deployment rendered successfully into a temporary target
- live deployment has now been performed
- current live config is repo-managed and backup-first
- latest backup directory:
  - `~/.openclaw/backups/20260317-101902/`
- live gateway restart completed successfully after deploy
- current live config includes:
  - pinned plugin allowlist
  - AgentSlam shared skill sync
  - lower-concurrency token-efficiency defaults
  - shorter session reset windows
  - shorter cron session retention
  - compact-state-first workspace guidance

## Current result

- the current live Telegram + Codex chain is still working
- ACPX runtime is loaded and ready
- the deployed config is both stricter and lower-noise than the old live config
