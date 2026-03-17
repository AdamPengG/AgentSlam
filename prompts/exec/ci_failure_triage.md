# CI Failure Triage

You are running inside `/home/peng/AgentSlam` as a Codex failure-triage task.

## Goal

Read the provided failing log path or artifact directory and produce the smallest credible diagnosis plus the next action.

## Read First

1. the primary failing input path listed in the runtime context
2. `docs/EVAL.md`
3. `docs/INTERFACES.md`
4. `docs/DATAFLOW.md`
5. `reports/SETUP_BLOCKERS.md`

## Required Output

- write the final markdown directly to the report path provided in the runtime context
- include:
  - failing stage or command
  - probable failure class
  - concrete evidence you used
  - smallest next fix or investigation step
  - whether the issue looks environmental, operational, or code-related

## Do Not

- do not fix code in this task
- do not guess when the logs are insufficient
- do not recommend broad refactors

## Style

- terse and specific
- operator-ready
- use exact paths whenever possible
