# OpenClaw Backup Status

## Existing live-config backups found

- `~/.openclaw/openclaw.json.pre_codex_resume_fix_20260317_075148`
- `~/.openclaw/openclaw.json.pre_upgrade_20260317_074326`
- `~/.openclaw/openclaw.json.pre_codex_fix_20260316_232645`
- `~/.openclaw/openclaw.json.bak_hardening`
- `~/.openclaw/openclaw.json.bak`

## New repo-side backup policy

- `ops/openclaw/bin/deploy_openclaw.sh` writes backups under:
  - `~/.openclaw/backups/<timestamp>/openclaw.json`
  - `~/.openclaw/backups/<timestamp>/jobs.json`
- credentials, pairings, and model auth files are preserved in place

## Current decision

No live deployment was performed in this pass. Existing live backups remain the
rollback source of truth until the first repo-managed deploy is approved.
