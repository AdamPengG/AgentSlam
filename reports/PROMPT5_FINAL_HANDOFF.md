# Prompt 5 Final Handoff

## What Was Completed

Prompt 5 converted the repo from an interactive-only setup into a near-24x7 Codex-only ops scaffold.

Completed in-repo work:

- added the `ops_dev` role in `.codex`
- expanded `AGENTS.md` with review, ops, artifact, and `codex exec` rules
- added four repo-local skills under `.agents/skills/`
- added five exec prompt templates under `prompts/exec/`
- added `scripts/ops/` wrappers for auth checks, locking, Codex execution, nightly evaluation, plan refresh, failure triage, and runner bootstrap
- added four GitHub workflow files under `.github/workflows/`
- added operator docs for Cloud setup, private-runner auth, self-hosted runner setup, MCP and skills, and the 24x7 runbook
- aligned `docs/PLANS.md`, `docs/EVAL.md`, `docs/INTERFACES.md`, `docs/DATAFLOW.md`, and `docs/TOOLS_AND_AGENT_PRACTICES.md` with the new ops reality

## What Is Now Locally Runnable

- auth preflight:
  - `bash scripts/ops/check_codex_auth.sh`
- safe runner scaffold:
  - `bash scripts/ops/bootstrap_self_hosted_runner.sh`
- locked non-interactive Codex execution:
  - `bash scripts/ops/run_codex_exec.sh --prompt prompts/exec/codex_smoke.md --report reports/PROMPT5_CODEX_SMOKE.md`
- repeatable nightly suite:
  - `bash scripts/ops/nightly_phase1_eval.sh --skip-codex-summary`
- plan refresh wrapper:
  - `bash scripts/ops/refresh_plan.sh`
- bounded failure triage wrapper:
  - `bash scripts/ops/triage_failure.sh --input <path>`

## What Is Repo-Ready But Still Needs Manual Activation

- Codex Cloud plus GitHub review features
- automatic reviews and `@codex review`
- self-hosted GitHub runner registration
- live scheduled workflow execution from GitHub Actions

These are documented, not blocked:

- `docs/CODEX_CLOUD_GITHUB_SETUP.md`
- `docs/SELF_HOSTED_RUNNER_SETUP.md`
- `docs/CODEX_AUTH_PRIVATE_RUNNER.md`
- `docs/OPERATOR_RUNBOOK_24X7.md`

## Validation Summary

- shell syntax: PASS
- workflow YAML parse: PASS
- script help entrypoints: PASS
- auth check: PASS
- self-hosted runner bootstrap scaffold: PASS
- minimal `codex exec` smoke: PASS
- nightly Phase 1 suite with build, unit tests, fixture, and bridge smoke: PASS

Primary evidence:

- `reports/PROMPT5_VALIDATION.md`
- `reports/PROMPT5_AUTH_CHECK.md`
- `reports/PROMPT5_CODEX_SMOKE.md`
- `reports/nightly/latest_suite.md`
- `reports/nightly/latest_summary.md`

## Added Files

### Config And Rules

- `.codex/agents/ops-dev.toml`
- `.codex/config.toml`
- `AGENTS.md`

### Skills

- `.agents/skills/phase1-fixture-acceptance/SKILL.md`
- `.agents/skills/isaac-office-nova-audit/SKILL.md`
- `.agents/skills/nightly-report-writer/SKILL.md`
- `.agents/skills/ci-failure-triage/SKILL.md`

### Prompt Files

- `prompts/exec/nightly_phase1_eval.md`
- `prompts/exec/plan_refresh.md`
- `prompts/exec/ci_failure_triage.md`
- `prompts/exec/nightly_handoff.md`
- `prompts/exec/codex_smoke.md`

### Ops Scripts

- `scripts/ops/common.sh`
- `scripts/ops/check_codex_auth.sh`
- `scripts/ops/with_codex_lock.sh`
- `scripts/ops/run_codex_exec.sh`
- `scripts/ops/phase1_ci_suite.sh`
- `scripts/ops/nightly_phase1_eval.sh`
- `scripts/ops/refresh_plan.sh`
- `scripts/ops/triage_failure.sh`
- `scripts/ops/bootstrap_self_hosted_runner.sh`

### Workflows

- `.github/workflows/robotics-ci.yml`
- `.github/workflows/nightly-phase1.yml`
- `.github/workflows/codex-plan-refresh.yml`
- `.github/workflows/codex-triage.yml`

### Documentation

- `docs/OPS_24X7_ARCHITECTURE.md`
- `docs/MCP_AND_SKILLS_SETUP.md`
- `docs/CODEX_CLOUD_GITHUB_SETUP.md`
- `docs/SELF_HOSTED_RUNNER_SETUP.md`
- `docs/CODEX_AUTH_PRIVATE_RUNNER.md`
- `docs/OPERATOR_RUNBOOK_24X7.md`

### Reports

- `reports/PROMPT5_STARTING_STATE.md`
- `reports/PROMPT5_AUTH_CHECK.md`
- `reports/PROMPT5_CODEX_SMOKE.md`
- `reports/PROMPT5_VALIDATION.md`
- `reports/PROMPT5_FINAL_HANDOFF.md`

## 5 To 10 Minute Next Checklist

1. read `docs/CODEX_CLOUD_GITHUB_SETUP.md`
2. connect GitHub inside ChatGPT or Codex
3. run `bash scripts/ops/bootstrap_self_hosted_runner.sh`
4. register the self-hosted runner with label `agentslam`
5. run `bash scripts/ops/check_codex_auth.sh`
6. run `bash scripts/ops/nightly_phase1_eval.sh`
7. confirm `reports/nightly/latest_summary.md`
8. open a small PR and trigger `@codex review`

## If You Want Nightly And PR Review Enabled Right Now

Recommended order:

1. complete GitHub connection in ChatGPT or Codex
2. register the self-hosted runner
3. verify local auth with `check_codex_auth.sh`
4. manually run `nightly-phase1` once
5. confirm artifacts and reports land as expected
6. then enable automatic review or start with `@codex review`

## Remaining Steps To Reach Near-24x7

- manual Cloud activation
- manual self-hosted runner registration
- one fully Codex-generated nightly summary and handoff run without `--skip-codex-summary`
- one GitHub-triggered run of each workflow on the registered runner

## Prompt 6 Recommendation

Yes. A focused Prompt 6 would be:

- validate the first real GitHub-triggered runner cycle
- run one full nightly with Codex-generated summary and handoff
- run one `refresh_plan.sh` and one `triage_failure.sh` from workflow entrypoints
