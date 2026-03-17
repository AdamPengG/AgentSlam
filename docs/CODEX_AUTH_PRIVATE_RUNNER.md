# Codex Auth On A Private Runner

## Current Repo Assumption

AgentSlam Prompt 5 uses ChatGPT-managed Codex auth on a trusted private runner. It does **not** require an API key for the current workflow.

## Why This Is The Current Path

- this machine already reports `codex login status` as logged in with ChatGPT
- Prompt 5 explicitly avoids API-key-based activation
- local runner tasks mainly need Codex for report generation, planning refresh, and bounded triage

## Local Auth Facts On This Machine

- expected Codex home: `~/.codex`
- observed auth file path: `~/.codex/auth.json`
- current quick check:

```bash
codex login status
```

## Recommended Login Flow

### Interactive Machine

If the runner user can open a browser:

```bash
codex login
```

### Headless Or Remote Machine

If the runner user is remote or browserless:

```bash
codex login --device-auth
```

That keeps the flow compatible with headless trusted runners.

## File-Backed Credential Guidance

- default auth file: `~/.codex/auth.json`
- default config path: `~/.codex/config.toml`
- if you relocate Codex state, set `CODEX_HOME` explicitly for the runner user
- back up `CODEX_HOME` carefully if the runner host is ephemeral, but keep permissions tight

## Why Concurrent Sharing Is Dangerous

Avoid multiple machines or concurrent jobs sharing one auth state because:

- file-backed auth state can be mutated during refresh
- concurrent refresh or write patterns are harder to reason about
- the operational blast radius is higher when one auth state backs multiple worker hosts

For Prompt 5, the safe rule is:

- one trusted runner host per auth state
- one active `codex exec` at a time per auth state

That is why the repo now uses:

- local `flock` via `scripts/ops/with_codex_lock.sh`
- workflow `concurrency` for codex-bearing GitHub Actions jobs

## When This Auth Model Is A Bad Fit

This model is not ideal when:

- you need a large elastic runner fleet
- you need multiple machines to consume one shared identity
- you need completely stateless ephemeral workers
- your organization requires centrally managed machine credentials instead of user-bound sign-in

In those cases, treat a different authentication architecture as a future design decision instead of forcing it into Prompt 5.

## Minimal Health Checks

```bash
bash scripts/ops/check_codex_auth.sh
bash scripts/ops/run_codex_exec.sh \
  --prompt prompts/exec/plan_refresh.md \
  --report reports/plan_refresh/manual-smoke.md
```

If the auth check passes but `run_codex_exec.sh` fails, inspect:

- `artifacts/ops/codex/`
- `reports/plan_refresh/`
- `~/.codex/log/`
