# Tools And Agent Practices

## Primary MCP And Analysis Tool

- GitNexus is the primary code-understanding MCP for this repo
- use it before broad refactors or cross-repo adapter work
- fall back to targeted file reads only after GitNexus or CLI-based narrowing

## Rule Placement

- long-lived project rules belong in `AGENTS.md`
- phase-specific architecture and interface rules belong in `docs/`
- reports capture one-run evidence and blockers

## Repo-Scoped Skills

- only create repo-scoped skills when a repeated workflow is stable and clearly worth preserving
- do not create skills just to mirror one prompt
- keep repo-scoped skills narrow and tied to repeatable acceptance, audit, summary, or triage flows

## Multi-Agent Coordination

- parallelize research and reading when safe
- keep one main writer per implementation-heavy directory
- require tester evidence before declaring a phase done
- let `ops_dev` own workflows, prompts, runner docs, and automation scripts so other roles do not invent private ops conventions

## Current Practice Decision

- Prompt 5 now adds repo-scoped skills for:
  - Phase 1 fixture acceptance
  - Isaac Office plus Nova audit
  - nightly report writing
  - CI failure triage
- `AGENTS.md`, `docs/`, `scripts/`, and `reports/` remain the source of truth; the new skills only wrap workflows that are already stable enough to preserve
