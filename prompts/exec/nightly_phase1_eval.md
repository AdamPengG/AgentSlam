# Nightly Phase 1 Eval

You are running inside `/home/peng/AgentSlam` as a Codex non-interactive task.

## Goal

Read the latest Phase 1 nightly suite evidence and write an operator-facing summary report.

## Read First

1. the runtime context appended by the wrapper
2. the summary-input file path listed there
3. the suite report path listed there
4. the precomputed delta path listed there
5. the previous nightly summary only if the runtime context provides one

## Required Output

- write the final markdown directly to the report path provided in the runtime context
- the report should explicitly mention:
  - build result
  - unit test result
  - fixture result
  - bridge smoke result if present
  - any blocker or regression signal
  - any lightweight difference from the previous nightly if a previous summary path is provided

## Do Not

- do not edit source code
- do not modify `ros_ws/src/`
- do not invent missing evidence
- do not claim Cloud activation or live Isaac bridge success unless the runtime inputs prove it
- do not read raw log files or re-diff artifact directories unless the suite report shows a failing stage

## Style

- concise and operator-friendly
- separate facts from recommendations
- prefer paths and exact stage names over generic commentary
