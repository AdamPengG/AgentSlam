# OpenClaw Security Audit Baseline

## Current live audit summary

- critical: 1
- warn: 3
- info: 1

## Critical findings

1. `plugins.allow` is unset while a local extension exists under `~/.openclaw/extensions`

## Warn findings

1. `gateway.trustedProxies` is empty
2. the live trust model is still effectively personal-assistant plus permissive runtime/fs access
3. extension plugin tools may be reachable under permissive tool policy

## Additional live observations

- `~/.openclaw/credentials` was tightened from `775` to `700` during this pass
- browser control is active on the current live gateway
- Telegram DM works, but groups are not usefully configured
- the live cron store is empty, which is safer than unknown scheduled work

## Repo-side mitigation direction

- pin `plugins.allow`
- disable browser and canvas by config
- disable groups for Telegram
- keep heartbeat at `0m`
- move to wrapper-script-driven cron only
