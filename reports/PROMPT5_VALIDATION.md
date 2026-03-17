# Prompt 5 Validation

## Scope

This report records the actual checks performed for the Prompt 5 24x7 Codex-only ops scaffold.

## Static Checks

### Shell Syntax

Command:

```bash
bash -n scripts/ops/*.sh scripts/*.sh
```

Result:

- PASS

### Workflow YAML Parse

Command:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml
for path in Path('.github/workflows').glob('*.yml'):
    with path.open('r', encoding='utf-8') as fh:
        yaml.safe_load(fh)
    print(path)
PY
```

Result:

- PASS
- parsed:
  - `.github/workflows/robotics-ci.yml`
  - `.github/workflows/nightly-phase1.yml`
  - `.github/workflows/codex-plan-refresh.yml`
  - `.github/workflows/codex-triage.yml`

### Script Help Entrypoints

Command:

```bash
for f in scripts/ops/*.sh; do
  bash "$f" --help >/dev/null
done
```

Result:

- PASS

### ShellCheck

Result:

- SKIPPED
- reason: `shellcheck` is not installed on this machine

## Auth And Runner Checks

### Codex Auth Check

Command:

```bash
bash scripts/ops/check_codex_auth.sh --report-path reports/PROMPT5_AUTH_CHECK.md
```

Result:

- PASS
- evidence:
  - `reports/PROMPT5_AUTH_CHECK.md`
- observed facts:
  - `codex --version` returned `codex-cli 0.114.0`
  - `codex login status` returned `Logged in using ChatGPT`
  - `~/.codex/auth.json` exists on this machine

### Self-Hosted Runner Bootstrap Scaffold

Command:

```bash
bash scripts/ops/bootstrap_self_hosted_runner.sh
```

Result:

- PASS
- evidence:
  - `artifacts/ops/self_hosted_runner_bootstrap/bootstrap_report.md`
  - `artifacts/ops/self_hosted_runner_bootstrap/service/agentslam-runner.service`

## Codex Exec Smoke

Command:

```bash
bash scripts/ops/run_codex_exec.sh \
  --prompt prompts/exec/codex_smoke.md \
  --report reports/PROMPT5_CODEX_SMOKE.md \
  --label codex_smoke \
  --exec-timeout 180
```

Result:

- PASS
- evidence:
  - `reports/PROMPT5_CODEX_SMOKE.md`
  - `artifacts/ops/codex/20260316-210214/codex_smoke_events.jsonl`
  - `artifacts/ops/codex/20260316-210214/codex_smoke_meta.txt`

What this proves:

- checked-in prompt files can drive `codex exec`
- auth preflight succeeded
- lock wrapper path worked
- final markdown report writing worked
- event logs and metadata were persisted under `artifacts/ops/codex/`

## Nightly Phase 1 Suite

Command:

```bash
bash scripts/ops/nightly_phase1_eval.sh --skip-codex-summary
```

Result:

- PASS
- suite evidence:
  - `reports/nightly/phase1_suite_20260316-210512.md`
  - `reports/nightly/latest_suite.md`
  - `reports/nightly/latest_summary.md`
  - `artifacts/nightly/20260316-210512/`

Observed suite status:

- build: PASS
- unit tests: PASS
- fixture: PASS
- bridge smoke: PASS

Captured nightly outputs:

- `artifacts/nightly/20260316-210512/captured/synthetic_semantic_map.json`
- `artifacts/nightly/20260316-210512/captured/query_chair.json`
- `artifacts/nightly/20260316-210512/captured/query_table.json`
- `artifacts/nightly/20260316-210512/captured/phase0_bridge_topics.txt`
- `artifacts/nightly/20260316-210512/captured/phase0_bridge_detection_sample.txt`
- `artifacts/nightly/20260316-210512/captured/phase0_bridge_odom_sample.txt`

## Limits

- a full Codex-generated nightly summary plus handoff was not exercised in the same run because the acceptance run used `--skip-codex-summary` after separately verifying `codex exec` with a smaller smoke prompt
- `refresh_plan.sh` and `triage_failure.sh` were validated indirectly through:
  - script syntax and help checks
  - the shared `run_codex_exec.sh` smoke path
- GitHub-side execution was not run because no self-hosted runner registration or remote workflow activation was performed from this prompt
