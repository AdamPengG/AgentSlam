# OpenClaw Phase Automation Plan

## OpenClaw bootstrap phase

1. validate repo-side config
2. dry-run deploy
3. tighten live security baseline
4. pin Telegram DM policy
5. keep cron empty until validation is complete

## Phase 0 automation hooks

- wrapper: `ops/openclaw/bin/agentslam_phase0_check.sh`
- report target: `reports/openclaw/` plus existing Phase 0 reports

## Phase 1 automation hooks

- fixture wrapper: `ops/openclaw/bin/agentslam_phase1_fixture.sh`
- replay wrapper: `ops/openclaw/bin/agentslam_phase1_replay_eval.sh`
- build wrapper: `ops/openclaw/bin/agentslam_build.sh`
- completion gate: `ops/openclaw/bin/agentslam_completion_gate.sh`

## Cron candidates

- `planner_cycle`: every 4h
- `nightly_eval`: once nightly
- `completion_gate`: after nightly
- `daily_handoff`: once daily
