# OpenClaw Token Efficiency Validation

## What Was Verified

- repo-side config renders cleanly
- repo-side config validates cleanly in a temporary home
- live deployment completed with backup-first behavior
- OpenClaw gateway restarted successfully
- ACPX runtime loaded successfully after restart
- Telegram channel remained enabled and running
- wrapper status and doctor commands remained usable after env-aware fixes

## Evidence

- backup directory:
  - `~/.openclaw/backups/20260317-101902/`
- live config:
  - `~/.openclaw/openclaw.json`
- compact state briefing:
  - `reports/openclaw/CURRENT_STATE.md`
- token-efficiency design note:
  - `reports/openclaw/TOKEN_EFFICIENCY_MODE.md`

## Live Effective Values

- default model: `codex-cli/gpt-5.3-codex`
- coder model: `codex-cli/gpt-5.4`
- evaluator model: `codex-cli/gpt-5.4`
- planner model: `codex-cli/gpt-5.3-codex`
- reporter model: `codex-cli/gpt-5.3-codex`
- maxConcurrent: `1`
- subagents.maxConcurrent: `1`
- direct idle reset: `90`
- global idle reset: `120`
- cron session retention: `6h`
- plugins allowlist:
  - `acpx`
  - `telegram`
  - `memory-core`

## Operational Outcome

The OpenClaw control plane is now configured to spend fewer tokens on routine
planning, reporting, and stale context carryover, while preserving a heavier
path for real coding and evaluation work.
