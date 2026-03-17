---
name: phase1-fixture-acceptance
description: Use this skill when you need to run or audit the Phase 1 fixture-based semantic mapping loop and confirm that expected artifacts and reports were produced.
---

# Phase 1 Fixture Acceptance

## Trigger

Use this skill when:

- validating that the Phase 1 fixture baseline still works
- preparing nightly or pre-merge acceptance evidence
- checking whether fixture outputs, query outputs, and runtime summaries landed in the expected paths

## Do Not Trigger

Do not use this skill when:

- the task is about live Isaac ROS bridge debugging
- the task is only about room graph or navigation work
- the task needs broad code refactors rather than regression evidence

## Inputs

- fixture path, usually `fixtures/semantic_mapping/synthetic_gt_pose_scene.json`
- mapper entrypoint or wrapper script, usually `scripts/run_phase1_fixture.sh`
- expected artifact directory, usually `artifacts/phase1/`
- optional report output path under `reports/`

## Outputs

- semantic map JSON confirmation
- query artifact confirmation
- runtime summary or command evidence
- concise pass/fail notes written under `reports/`

## Workflow

1. Read `docs/PHASE1_SEMANTIC_MAPPING.md`, `docs/EVAL.md`, and the latest `reports/PHASE1_VALIDATION.md`.
2. Run `bash scripts/run_phase1_fixture.sh` unless the task is audit-only.
3. Confirm these outputs exist and are fresh enough for the task:
   - `artifacts/phase1/synthetic_semantic_map.json`
   - `artifacts/phase1/query_chair.json`
   - `artifacts/phase1/query_table.json`
4. If the task asks for broader acceptance, pair this with at least one build or smoke check.
5. Write a short report that states:
   - command run
   - artifact paths checked
   - pass/fail result
   - any blockers or drift

## Notes

- Prefer rerunning the checked-in script over recreating the command by hand.
- Keep this skill focused on acceptance evidence, not on changing mapper behavior.
