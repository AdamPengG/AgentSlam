---
name: ci-failure-triage
description: Use this skill when CI, nightly validation, build, test, or fixture jobs fail and you need a bounded diagnosis plus the smallest sensible next step.
---

# CI Failure Triage

## Trigger

Use this skill when:

- a workflow job failed
- `colcon build` failed
- unit tests failed
- fixture export or replay acceptance failed
- a nightly run produced logs that need diagnosis

## Do Not Trigger

Do not use this skill when:

- there is no log, report, or artifact evidence to inspect
- the task is a planned feature implementation
- the request is for a full refactor instead of a bounded diagnosis

## Inputs

- failing log path or report directory
- latest relevant docs:
  - `docs/EVAL.md`
  - `docs/INTERFACES.md`
  - `docs/DATAFLOW.md`
- latest blocker tracker:
  - `reports/SETUP_BLOCKERS.md`

## Outputs

- a markdown triage report under `reports/triage/` or another requested `reports/` path
- a likely failure category
- the minimum next investigation or fix step

## Workflow

1. Read the smallest set of logs needed to identify the failing stage.
2. State the failing command or stage exactly.
3. Classify the failure:
   - environment
   - dependency
   - build
   - test regression
   - artifact contract drift
   - operator/setup gap
4. Propose the smallest credible next action.
5. Do not directly rewrite business logic unless the task explicitly asks for a fix.

## Notes

- Triage should narrow the problem, not pretend it is solved.
- If the evidence is insufficient, say what is missing instead of guessing.
