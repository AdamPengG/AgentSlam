# Telegram Reply Stability

Date: 2026-03-17

## Symptom

OpenClaw remained online, but automatic Telegram replies intermittently failed with:

- `Polling stall detected`
- `sendChatAction failed`
- `sendMessage failed`

Manual `openclaw message send` still succeeded, which indicates the bot and account were healthy while the automatic reply path was more fragile under live polling conditions.

## Mitigation Applied

- Set `agents.defaults.typingMode` to `never` to avoid repeated typing-indicator requests.
- Set `channels.telegram.streamMode` to `off` to disable Telegram draft streaming.
- Set `channels.telegram.timeoutSeconds` to `30`.
- Set `channels.telegram.retry` to a more conservative retry policy.
- Set `channels.telegram.network.autoSelectFamily` to `false`.
- Set `channels.telegram.proxy` explicitly to `${HTTPS_PROXY}` so Telegram Bot API calls use the intended HTTP proxy directly.
- Updated `ops/openclaw/bin/common.sh` so local operator wrappers inherit the same proxy-related service environment as the live gateway.

## Expected Effect

- Fewer Telegram API calls during long replies.
- Less exposure to polling + typing + draft-stream combinations that were triggering failures.
- More deterministic Telegram network behavior on this host.

## Validation

- Repo-side OpenClaw config validated successfully after the change.
- Live deploy completed successfully and the gateway restarted cleanly.
- Post-change manual Telegram send probe succeeded.
- `openclaw_status.sh` now succeeds with the same proxy-aware environment as the service.
- Immediate post-restart logs show `autoSelectFamily=false (config)` for Telegram.
- No new `Polling stall` or `sendMessage failed` entries appeared during the first short monitoring window after restart.

## Remaining Risk

This mitigates the most likely instability path but does not prove perfect long-poll reliability under every network condition. If failures continue, the next likely action is to remove `ALL_PROXY`/SOCKS from the service environment for Telegram-related traffic and keep only explicit HTTP proxy routing.
