# MCP And Skills Setup

## Current MCP Strategy

AgentSlam keeps GitNexus as the primary MCP for code understanding, impact analysis, and execution-flow tracing.

## Current Project Config

The project-level Codex config already declares GitNexus in [config.toml](/home/peng/AgentSlam/.codex/config.toml):

- server name: `gitnexus`
- command: `npx`
- args: `["-y", "gitnexus@latest", "mcp"]`

This means the repo is already set up to request a GitNexus MCP server when the project config is loaded.

## Trusted Project Requirement

Project-level `.codex/config.toml` is only loaded when this repository is opened as a trusted project. If the project is not trusted, repo-specific agent and MCP configuration may not activate.

## CLI And IDE Behavior

- Codex CLI and the IDE extension use the same style of MCP configuration
- project-level config is the right place for repo-specific MCP declarations
- repo-local settings should stay minimal and explicit so they do not surprise operators when trust is enabled

## Why GitNexus Stays First

- the repo already has a live GitNexus config and an up-to-date local index
- Prompt 5 is about durable engineering operations, not replacing the existing analysis tool
- GitNexus fits both interactive and `codex exec` workflows because it reduces blind search before edits or triage

## Repo-Local Skills Location

Prompt 5 standardizes repo-local skills under:

- `.agents/skills/`

This keeps repeatable repository workflows versioned with the project while avoiding drift between prompt conventions and operator docs.

## Included Skills

- `.agents/skills/phase1-fixture-acceptance/`
- `.agents/skills/isaac-office-nova-audit/`
- `.agents/skills/nightly-report-writer/`
- `.agents/skills/ci-failure-triage/`

## Skill Use Rules

- use a repo-local skill when the task matches its trigger conditions
- do not invoke a skill just because it exists
- keep skills narrow and reusable
- if a workflow is still unstable, prefer plain docs and scripts until the pattern settles

## Future Options

- add a docs-oriented MCP only if it materially improves operator workflows without introducing brittle setup dependencies
- keep future MCP additions behind the same trusted-project and operator-doc expectations used for GitNexus
