# AgentSlam Working Rules

## Scope

This repository is an integration workspace for AgentSlam. Phase 0 is reserved for infrastructure, workspace scaffolding, documentation, and validation setup. Do not rush into full algorithm implementation.

## Repository Boundaries

- `refs/` contains upstream reference repositories and is read-only from the perspective of this repo.
- Do not make business changes inside `refs/`, and do not include `refs/` in main-repo commits.
- Treat `/home/peng/AgentSlam` as the project root for all scripts, reports, and generated documentation.

## Technical Direction

- Start with GT pose as the localization source; replacing localization belongs to a later phase.
- The default sensing stack is visual plus IMU only. Do not enable LiDAR by default.
- Favor standard ROS 2 messages and established packages early. Introduce custom messages only when the integration benefit is clear and documented.
- Isaac office scenes and a Nova wheeled robot are the preferred simulation baseline until a change is explicitly approved.

## Documentation Contracts

- Any important interface change must update `docs/INTERFACES.md` and `docs/DATAFLOW.md` in the same workstream.
- Planning or evaluation changes must keep `docs/PLANS.md` and `docs/EVAL.md` aligned with current assumptions.
- Record environment blockers and unresolved setup gaps in `reports/SETUP_BLOCKERS.md`.

## Verification Gates

- Any mergeable change must pass at least one build, one smoke check, and one replay or static validation pass.
- Keep verification evidence in `reports/` instead of only printing terminal output.
- Scripts should be repeatable, conservative, and safe to rerun.

## Review Guidelines

- For `@codex review` or any review-only task, prioritize correctness bugs, regression risks, interface drift, missing validation, and operational hazards before style feedback.
- Review findings should cite exact files and explain user-facing or operator-facing impact.
- If no actionable findings are discovered, say so explicitly and call out any remaining test or environment gaps.

## Multi-Agent Coordination

- Only one write-heavy agent may make large edits under `ros_ws/src` at a time.
- Planning and research roles should prefer documentation outputs over code edits.
- Bridge, mapping, navigation, and test work should converge through documented interfaces instead of private assumptions.
- Use GitNexus as the primary code-understanding MCP before broad cross-repo edits.
- Long-lived workflow rules belong in `AGENTS.md` and `docs/`; repo-scoped skills should be created only after a workflow is stable and repeatedly useful.
- `ops_dev` owns `.github/workflows/`, `scripts/ops/`, `prompts/exec/`, runner/auth runbooks, and repo-local automation skills.
- Nightly or autonomous agents must not modify `ros_ws/src/` unless the active prompt explicitly authorizes development changes there.

## Ops And Automation Rules

- Prefer Codex Cloud plus GitHub integration for review, planning, and background task entry points; prefer trusted private runners plus `codex exec` for local build, test, and report generation.
- Treat ChatGPT-managed Codex auth as private-runner state. Do not assume one `auth.json` can be shared safely across multiple machines or concurrent jobs.
- Any automation path that invokes `codex exec` must serialize access with a lock or workflow `concurrency` group.
- Nightly jobs default to writing `reports/`, `artifacts/`, and necessary log directories only. They must not directly rewrite business source files during routine runs.
- Store repeatable prompt templates in `prompts/exec/` and repo-scoped skills in `.agents/skills/`.
- Never hardcode secrets, tokens, or runner registration material in the repository.

## Artifact Conventions

- Human-readable execution summaries belong in `reports/`.
- Nightly summaries belong in `reports/nightly/`.
- Plan refresh outputs belong in `reports/plan_refresh/`.
- Failure-triage outputs belong in `reports/triage/`.
- Machine-generated logs and captured runtime artifacts belong under `artifacts/`, with autonomous/nightly runs using `artifacts/nightly/` or `artifacts/ops/`.

## Codex Exec Contract

- Every `codex exec` run must have:
  - a checked-in prompt file under `prompts/exec/`
  - a deterministic output report path
  - a persisted final message or handoff report
  - a JSONL or text log captured under `artifacts/`
- `codex exec` jobs should read the minimal required docs and reports first, then write a concise handoff artifact instead of only printing to stdout.
- When auth is unavailable, scripts should fail clearly and leave the workspace unchanged aside from diagnostic reports or logs.

## Skill Placement

- Repo-local skills for this project live under `.agents/skills/`.
- Skills should describe trigger conditions, non-trigger conditions, required inputs, expected outputs, and any helper scripts they rely on.

## Git Hygiene

- Do not guess `git user.name` or `git user.email`; if either is missing, stop before commit or push and write a setup report.
- Do not push unless explicitly requested.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **AgentSlam** (77136 symbols, 133043 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/AgentSlam/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/AgentSlam/context` | Codebase overview, check index freshness |
| `gitnexus://repo/AgentSlam/clusters` | All functional areas |
| `gitnexus://repo/AgentSlam/processes` | All execution flows |
| `gitnexus://repo/AgentSlam/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## CLI

- Re-index: `npx gitnexus analyze`
- Check freshness: `npx gitnexus status`
- Generate docs: `npx gitnexus wiki`

<!-- gitnexus:end -->
