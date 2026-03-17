# OpenClaw Telegram Status

## Live channel state

- channel: Telegram default
- status: enabled, configured, running
- transport: polling
- token source: config/env-backed
- outbound reply path: repaired on 2026-03-17 after Node proxy handling fix

## Live access policy

- DM policy: pairing
- group policy: currently not useful in the live config and should not be used

## Repo-side target policy

- bootstrap: `dmPolicy: pairing`
- steady state: `dmPolicy: allowlist`
- groups: disabled

## Remaining operator dependency

- the numeric Telegram user id still needs to be pinned in local-only secrets
- operator allowlist already includes `7051856936`
- service-level outbound send was validated after the repair

## Known Incident And Resolution

- symptom:
  - inbound Telegram messages reached OpenClaw
  - final replies failed with `sendMessage failed`
- root cause:
  - Node traffic from the gateway was not honoring the proxy path correctly
  - Telegram API requests hit a TLS-mismatched route
- fix:
  - systemd drop-in added `NODE_USE_ENV_PROXY=1`
  - see `reports/openclaw/TELEGRAM_REPLY_FIX.md`
