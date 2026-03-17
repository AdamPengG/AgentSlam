# OpenClaw Cross-Channel Session Sync

Date: 2026-03-17

## Goal

Make direct messages from WebChat and Telegram share one conversation for a single-user setup.

## Changes

- Switched `session.dmScope` from `per-channel-peer` to `main`.
- Added explicit `bindings` so both `webchat` and `telegram` route to the `planner` agent.
- Kept the AgentSlam `planner` workspace as the single long-lived control-plane brain.

## Expected Behavior

- Future direct messages from WebChat and Telegram resolve to `agent:planner:main`.
- Replies from either channel continue the same planner conversation instead of splitting by channel.
- Old legacy sessions may still remain on disk for audit/reset purposes, but new traffic should converge to one shared main thread.

## Validation

- Live config now shows `session.dmScope = "main"`.
- Live config now contains `bindings` routing both `webchat` and `telegram` to `planner`.
- Planner session store now uses `agent:planner:main` as the direct-message key.
- OpenClaw gateway was restarted successfully after deploy and remained `active`.
