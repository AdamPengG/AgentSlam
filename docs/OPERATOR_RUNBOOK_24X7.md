# Operator Runbook 24x7

## What This Runbook Covers

This is the day-to-day operating guide for the Prompt 5 automation layer. It assumes the repository is already checked out on a trusted Linux machine and that you want repeatable nightly validation without turning the repo into an API-key-driven system.

## Daily Checklist

1. Check the latest summary:
   - `reports/nightly/latest_summary.md`
2. If the nightly failed, check:
   - `reports/triage/latest.md`
3. If you need the full raw evidence, inspect:
   - `artifacts/nightly/`
4. If you suspect auth drift, run:

```bash
cd /home/peng/AgentSlam
bash scripts/ops/check_codex_auth.sh
```

## Weekly Checklist

1. Run a manual plan refresh:

```bash
cd /home/peng/AgentSlam
bash scripts/ops/refresh_plan.sh
```

2. Re-read:
   - `reports/plan_refresh/latest.md`
   - `reports/SETUP_BLOCKERS.md`
3. Decide whether blocked items should stay deferred or become the next focused prompt

## Manual Nightly Trigger

### Local Shell

```bash
cd /home/peng/AgentSlam
bash scripts/ops/nightly_phase1_eval.sh
```

### GitHub Actions

- open the `nightly-phase1` workflow
- use `Run workflow`
- confirm the target branch

## How To Read Failures

1. Open `reports/nightly/latest_suite.md`
2. Identify the first failing stage:
   - build
   - unit tests
   - fixture
   - bridge smoke
3. Open the matching log under the latest `artifacts/nightly/<timestamp>/logs/`
4. If you want Codex to summarize the failure path again:

```bash
cd /home/peng/AgentSlam
bash scripts/ops/triage_failure.sh --input artifacts/nightly/<timestamp>
```

## How To Ask Codex For Triage

Use the script wrapper rather than raw `codex exec`:

```bash
cd /home/peng/AgentSlam
bash scripts/ops/triage_failure.sh --input artifacts/nightly/<timestamp>
```

This preserves:

- auth checking
- locking
- saved prompt snapshot
- saved JSONL event log
- deterministic report output

## How To View Current Reports

- architecture:
  - `docs/OPS_24X7_ARCHITECTURE.md`
- auth:
  - `docs/CODEX_AUTH_PRIVATE_RUNNER.md`
- runner setup:
  - `docs/SELF_HOSTED_RUNNER_SETUP.md`
- Cloud and GitHub:
  - `docs/CODEX_CLOUD_GITHUB_SETUP.md`
- latest nightly:
  - `reports/nightly/latest_suite.md`
  - `reports/nightly/latest_summary.md`
  - `reports/nightly/latest_handoff.md`
  - the latest nightly artifact directory for `nightly_delta.md`
- latest plan refresh:
  - `reports/plan_refresh/latest.md`

## Pause Or Resume Automation

### Pause Scheduled GitHub Nightlies

- disable the `nightly-phase1` workflow in GitHub Actions
- or stop the self-hosted runner service temporarily

### Resume Scheduled GitHub Nightlies

- re-enable the workflow in GitHub Actions
- restart the runner service if it was stopped
- run one manual nightly first if the runner was offline for a long time

## 5 To 10 Minute Bring-Up Checklist

1. `codex login status`
2. `bash scripts/ops/check_codex_auth.sh`
3. `bash scripts/ops/bootstrap_self_hosted_runner.sh`
4. connect GitHub in ChatGPT or Codex
5. register the GitHub self-hosted runner with label `agentslam`
6. run `bash scripts/ops/nightly_phase1_eval.sh`
7. confirm `reports/nightly/latest_summary.md` exists
8. trigger `@codex review` on a small PR
