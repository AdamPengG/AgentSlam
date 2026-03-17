# Nightly Handoff

You are running inside `/home/peng/AgentSlam` as a Codex handoff task after a nightly run.

## Goal

Turn the nightly evidence into a short handoff that the project owner can read in a minute.

## Read First

1. the runtime context appended by the wrapper
2. the suite report path listed there
3. the nightly summary path listed there
4. the precomputed delta path listed there if it exists

## Required Output

- write the final markdown directly to the report path provided in the runtime context
- include:
  - what completed
  - what failed or was skipped
  - whether follow-up is needed before the next scheduled run
  - the one most useful next action

## Do Not

- do not restate every log line
- do not edit code
- do not claim fixes that were not performed
- do not re-open raw logs unless the summary says a stage failed

## Style

- brief
- clear
- owner-facing rather than agent-facing
