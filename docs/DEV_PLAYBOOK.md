# Development Playbook

## Task Splitting

- start from the active phase goal, not from a tempting upstream capability
- prefer one main writer per implementation-critical directory
- let planning and research converge through docs before code fans out

## Change Strategy

- keep changes idempotent
- keep the offline fixture path working while expanding runtime hooks
- prefer narrow, testable increments over broad scaffolding bursts
- update docs whenever interface or phase boundaries change

## Branch And Commit Strategy

- local commits are encouraged at milestone boundaries
- push only with explicit approval
- do not mix `refs/` content into main repo history

## Offline-First Bias

- if a full GUI bring-up is uncertain, unblock core logic with fixtures or replay
- treat offline validation as a first-class deliverable, not a fallback after failure

## Avoiding Large Refactors

- preserve phase boundaries
- avoid custom messages until standard messages are clearly insufficient
- use placeholder packages and docs to reserve boundaries rather than implementing speculative systems
