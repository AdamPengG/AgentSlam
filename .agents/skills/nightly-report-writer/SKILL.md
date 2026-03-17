---
name: nightly-report-writer
description: Use this skill to turn nightly build, test, fixture, and codex-exec outputs into a consistent operator-facing summary.
---

# Nightly Report Writer

## Trigger

Use this skill when:

- a nightly run finished and needs a concise owner-facing report
- build, test, fixture, and query results need to be summarized in `reports/nightly/`
- you need to compare the latest nightly against the immediately previous one at a lightweight level

## Do Not Trigger

Do not use this skill when:

- the run itself has not collected logs or artifacts yet
- the task is a deep bugfix rather than reporting
- there is no concrete report path to write to

## Inputs

- latest nightly report directory under `reports/nightly/`
- latest artifact directory under `artifacts/nightly/`
- logs from build, tests, fixture, smoke, or codex exec
- previous nightly summary if present

## Outputs

- one markdown report with:
  - success items
  - failures or blockers
  - notable changes from the previous run
  - next-step recommendations

## Workflow

1. Read the current phase assumptions in `docs/PLANS.md`, `docs/EVAL.md`, and `docs/PHASE1_SEMANTIC_MAPPING.md`.
2. Read the newest logs and artifact indexes before summarizing.
3. Separate facts from inference:
   - facts from logs, files, return codes
   - inferences as clearly labeled operator guidance
4. Report only concrete deltas when comparing with an earlier nightly.
5. Avoid proposing risky code edits unless the task explicitly asks for them.

## Notes

- The report should help an operator decide whether to investigate, rerun, or move on.
- Keep the nightly report concise enough for daily use.
