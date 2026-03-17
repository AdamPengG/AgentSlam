# OpenClaw Security Model

## Trust boundary

OpenClaw is treated as a local, single-operator control plane with Telegram DM
as the only intended remote ingress.

## Mandatory controls

- `gateway.bind: "loopback"`
- token auth enabled
- Telegram groups disabled
- browser tool disabled
- canvas host disabled
- node-related tools denied
- `plugins.allow` pinned to an explicit list
- `tools.elevated.enabled: false`
- `tools.fs.workspaceOnly: true`
- heartbeat disabled
- cron used sparingly and only through wrapper scripts

## Current live risks found during baseline audit

- `~/.openclaw/credentials` is too permissive and should be `0700`
- browser control is active in the live config
- `plugins.allow` is unset in the live config
- an untracked `wecom-app` extension exists under `~/.openclaw/extensions`
- live cron store exists but has no controlled jobs yet

## Deployment posture

- Repo-side source may be stricter than the current live config.
- Live deployment should happen only after dry-run validation succeeds.
- Existing credentials and pairing state must be preserved across deployment.
