# agentslam-orchestrator

Use when the task is to drive the AgentSlam 24x7 loop rather than do one-off coding.

## Trigger

- plan the next bounded work cycle
- decide whether to implement, validate, report, or stop
- coordinate `planner -> coder -> evaluator -> reporter -> completion_gate`

## Do not use

- for direct package-level debugging without any orchestration need
- for free-form shell exploration outside approved wrapper scripts

## Required inputs

- current phase and blocker state
- latest reports under `reports/` and `reports/openclaw/`

## Workflow

1. read the latest status and blocker reports
2. pick exactly one bounded next action
3. route execution through `ops/openclaw/bin/agentslam_*.sh`
4. update reports before declaring progress
5. run the completion gate before notifying the operator

## Outputs

- updated plan or handoff report
- one bounded next-step decision
- explicit stop/wait state when user review is required
