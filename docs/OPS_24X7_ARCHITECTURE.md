# AgentSlam 24x7 Ops Architecture

## Goal

Turn the current Phase 1 baseline into a Codex-only workflow that can keep building, validating, summarizing, and triaging with minimal manual intervention, while keeping sensitive activation steps outside the repository.

## Starting Reality

- the repo already has a validated Phase 1 baseline:
  - `colcon build`
  - focused unit tests
  - fixture export
  - replay-backed smoke and demo scripts
- multi-agent role definitions exist for interactive work
- GitNexus MCP is already declared in project config and the local GitNexus index is current
- Codex CLI is installed locally and the current machine is logged in with ChatGPT-managed auth

## Adopted 24x7 Shape

### Cloud Layer

- use Codex Cloud plus GitHub integration for:
  - PR review
  - `@codex review`
  - `@codex ...` background tasks
  - lightweight planning or summary tasks initiated from GitHub
- this layer is intentionally documented as a hand-activated capability because repository changes alone cannot enable your account or organization settings

### Runner Layer

- use a trusted Linux self-hosted runner with local `codex exec` for:
  - `colcon build`
  - focused unit tests
  - fixture-based Phase 1 regression
  - nightly report generation
  - failure triage against local logs and artifacts
- all `codex exec` use must be serialized because ChatGPT-managed auth is file-backed and should not be contended by multiple jobs at once

### Repo Rules Layer

- keep long-lived workflow rules in `AGENTS.md`
- keep repeatable ops skills in `.agents/skills/`
- keep reusable prompt templates in `prompts/exec/`
- keep ops entrypoints in `scripts/ops/`
- keep validation evidence in `reports/` and machine outputs in `artifacts/`

### CI And Nightly Layer

- GitHub Actions defines the orchestration surface
- self-hosted runner labels default to:
  - `self-hosted`
  - `linux`
  - `agentslam`
- codex-bearing workflows must use workflow `concurrency`
- local scripts also use `flock` so the same serialization rule holds outside GitHub Actions

## Why This Prompt Does Not Use API Keys

- the requested operating model is explicitly Codex-only with ChatGPT-managed auth
- Phase 1 regression, planning refresh, and triage do not require OpenAI API integration to be useful
- avoiding API keys keeps the current repo closer to the operator workflow that already works on this machine

## Why Agents SDK Is Not A Current Dependency

- this repo does not need a new application-side agent runtime to get value from nightly validation and report generation
- the immediate gap is orchestration and operator hygiene, not another agent framework
- Codex Cloud plus `codex exec` already covers review, summarization, and controlled local execution for this phase

## Explicit Serialization Rule

- one runner machine should own one active ChatGPT-managed Codex auth state
- concurrent `codex exec` jobs on the same auth state must be serialized
- GitHub workflows use `concurrency`
- local scripts use `scripts/ops/with_codex_lock.sh`

## Artifact Contract

### Nightly

- reports:
  - `reports/nightly/`
- artifacts:
  - `artifacts/nightly/`

### Codex Exec Support Files

- prompt templates:
  - `prompts/exec/`
- codex logs:
  - `artifacts/ops/codex/`
- plan refresh:
  - `reports/plan_refresh/`
- failure triage:
  - `reports/triage/`

## What Is Deliverable In-Repo

- role definitions and repo rules
- reusable skills and prompts
- `codex exec` wrapper scripts
- nightly and triage shell entrypoints
- GitHub workflow YAML
- operator-facing docs for Cloud, runner, and auth setup

## What Still Requires Manual Activation

- connecting the repository in Codex Cloud or ChatGPT settings
- enabling GitHub-side review features such as automatic reviews
- registering a self-hosted runner in GitHub
- running `codex login` or `codex login --device-auth` on the trusted runner if the machine is not already authenticated

## Success Criteria For Prompt 5

- a trusted runner can run one locked `codex exec` task without editing business code
- a nightly shell entrypoint can run build, test, fixture validation, and write reports
- workflows and runbooks are complete enough that the remaining work is account activation, not repository invention
