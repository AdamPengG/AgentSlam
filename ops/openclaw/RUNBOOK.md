# OpenClaw Runbook

## Safe order

1. Audit the current live state:
   - `bash ops/openclaw/bin/openclaw_status.sh`
   - `bash ops/openclaw/bin/doctor_openclaw.sh`
2. Validate the repo-side source:
   - `bash ops/openclaw/bin/validate_openclaw.sh`
3. Dry-run deployment into a temporary home:
   - `bash ops/openclaw/bin/deploy_openclaw.sh --dry-run`
4. Review rendered output and backup plan in `reports/openclaw/`.
5. Deploy to the real `~/.openclaw` only after the dry-run is clean.

## Rollback

1. Locate the latest backup under `~/.openclaw/backups/`.
2. Restore `openclaw.json` and `cron/jobs.json` if needed.
3. Restart the user service:
   - `systemctl --user restart openclaw-gateway.service`
4. Re-run:
   - `openclaw config validate`
   - `openclaw channels status`

## Telegram bootstrap

1. Keep `dmPolicy: pairing` until the numeric Telegram user id is confirmed.
2. Use `bash ops/openclaw/bin/telegram_pairing_check.sh` to inspect status.
3. After the user id is known, store it in a local-only secret file or env var.
4. Switch the deployed config to `allowlist` for Telegram DMs.

## Cron rollout

1. Keep heartbeat disabled.
2. Start with no cron jobs in production.
3. Add only planner, nightly eval, completion gate, and daily handoff.
4. Keep GPU and simulation work serialized through `agentslam_lock.sh`.
