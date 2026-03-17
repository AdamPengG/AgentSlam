# OpenClaw Cron Status

## Live store

- `~/.openclaw/cron/jobs.json` exists
- current jobs: none

## Repo-side scheduler source

- scheduler fragment exists at `ops/openclaw/src/conf.d/cron.json5`
- current baseline:
  - `enabled: true`
  - `maxConcurrentRuns: 1`
  - `sessionRetention: 6h`
  - `runLog.maxBytes: 1mb`
  - `runLog.keepLines: 800`

## Planned first job set

- `planner_cycle`
- `nightly_eval`
- `completion_gate`
- `daily_handoff`

## Current decision

No cron jobs are deployed yet. This remains intentional so routine token use
stays event-driven rather than time-driven.
