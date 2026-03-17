# agentslam-nightly-eval

Use for repeatable nightly-style validation, report generation, and handoff.

## Trigger

- build/test/fixture/replay regression runs
- daily or nightly handoff generation

## Workflow

1. start from the existing validated shell paths
2. use `scripts/ops/nightly_phase1_eval.sh` or the OpenClaw wrappers
3. keep reports in `reports/nightly/`
4. keep machine logs in `artifacts/nightly/`

## Outputs

- suite report
- summary report
- handoff report
