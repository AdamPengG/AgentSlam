# agentslam-phase0-isaac-bridge

Use when checking or advancing the Isaac Sim Office + Nova baseline.

## Trigger

- Isaac install validation
- Office scene or Nova asset checks
- bridge smoke status
- Phase 0 bring-up reporting

## Do not use

- for semantic-map algorithm changes
- for editing anything under `refs/`, `GS4`, or Isaac install trees

## Required inputs

- `reports/ISAAC_DISCOVERY.md`
- `reports/openclaw/PATH_DISCOVERY.md`

## Workflow

1. run `bash ops/openclaw/bin/agentslam_phase0_check.sh`
2. capture logs and summarize blockers
3. prefer documenting gaps over guessing fixes in external read-only trees

## Outputs

- validation log paths
- phase0 status note
- smallest next action
