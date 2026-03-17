# OpenClaw Telegram Reply Fix

## Symptom

OpenClaw received Telegram messages and started Codex work, but failed to send
the final reply back to Telegram.

Observed gateway errors included:

- `sendMessage failed`
- `final reply failed`
- `Polling stall detected`

## Root Cause

The OpenClaw gateway runs on Node. On this machine, Node did not correctly use
the configured proxy environment by default. As a result, Telegram API requests
from Node reached a TLS-intercepted path and failed hostname verification.

Direct evidence from Node-based probes:

- `ERR_TLS_CERT_ALTNAME_INVALID`
- certificate altnames for `extern.facebook.com`
- requested host was `api.telegram.org`

By contrast, `curl` with the same proxy path succeeded, which isolated the
problem to Node proxy handling rather than Telegram credentials or chat policy.

## Fix Applied

A systemd drop-in was added for the live gateway service:

- `~/.config/systemd/user/openclaw-gateway.service.d/env-proxy.conf`

with:

```ini
[Service]
Environment=NODE_USE_ENV_PROXY=1
```

This makes Node/undici honor the configured proxy environment for Telegram API
traffic.

## Validation

- Node `fetch(getMe)` succeeds with `NODE_USE_ENV_PROXY=1`
- Node `fetch(sendMessage)` succeeds with `NODE_USE_ENV_PROXY=1`
- the OpenClaw gateway was reloaded and restarted after the drop-in was added

## Follow-Up

- keep the systemd drop-in in place for this machine
- if the gateway service is regenerated later, verify the drop-in still exists
- if Telegram errors reappear, inspect `journalctl --user -u openclaw-gateway.service`
