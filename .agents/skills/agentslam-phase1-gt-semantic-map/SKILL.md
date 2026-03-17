# agentslam-phase1-gt-semantic-map

Use when the work stays inside the GT-pose semantic-map baseline.

## Trigger

- fixture semantic-map validation
- replay semantic-map validation
- export/query artifact review

## Workflow

1. prefer `bash ops/openclaw/bin/agentslam_phase1_fixture.sh`
2. use `bash ops/openclaw/bin/agentslam_phase1_replay_eval.sh` for replay-backed checks
3. keep outputs under `artifacts/phase1/`
4. summarize results into `reports/`

## Guardrails

- keep GT pose as the localization source
- do not add LiDAR as the default sensing path
- keep query and artifact paths stable
