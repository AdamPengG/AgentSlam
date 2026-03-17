# Plan Refresh

You are running inside `/home/peng/AgentSlam` as a Codex non-interactive planning task.

## Goal

Refresh the current near-term plan and blocker summary from the latest project docs and reports.

## Read First

1. `reports/PROMPT5_STARTING_STATE.md`
2. `reports/SETUP_BLOCKERS.md`
3. `reports/PHASE1_VALIDATION.md`
4. `reports/PHASE1_REVIEW.md`
5. `docs/PLANS.md`
6. `docs/EVAL.md`
7. `docs/INTERFACES.md`
8. `docs/DATAFLOW.md`
9. any latest nightly summary path listed in the runtime context

## Required Output

- write the final markdown directly to the report path provided in the runtime context
- include:
  - current status snapshot
  - top blockers
  - recommended next 3 to 5 actions
  - anything in docs that looks out of sync with current evidence

## Do Not

- do not edit code
- do not rewrite docs directly
- do not suggest API-key-based architecture for the current phase
- do not broaden the plan into Phase 2 feature implementation

## Style

- short sections
- explicit priorities
- grounded in the files you read
