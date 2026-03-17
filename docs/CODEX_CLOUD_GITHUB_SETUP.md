# Codex Cloud GitHub Setup

## Purpose

This document covers the manual steps that cannot be completed from inside the repository but are required to activate Codex Cloud plus GitHub review workflows for AgentSlam.

## What This Repo Already Provides

- GitHub workflow files that assume a trusted self-hosted runner for local execution
- repo rules in `AGENTS.md`
- prompt templates in `prompts/exec/`
- locked `codex exec` wrappers in `scripts/ops/`

The repository does **not** connect your GitHub account or enable product-side review features for you.

## Before You Start

- the repository is already pushed to GitHub
- you can sign in to ChatGPT or Codex with the account that should own the integration
- if you plan to use local runner jobs too, make sure the trusted runner user can already run `codex login status`

## Manual Steps In ChatGPT Or Codex

1. Sign in to ChatGPT or Codex with the account that should own the review workflow.
2. Open the current Codex or ChatGPT settings flow for GitHub connection.
3. Connect the GitHub account that has access to the `AgentSlam` repository.
4. Approve the GitHub authorization flow for the repositories or scopes you want Codex to access.

Notes:

- OpenAI's current help guidance says Codex web requires connecting ChatGPT to your GitHub account.
- The exact settings labels may change, so follow the current product wording if it differs slightly from this doc.

## Enable Review Features

After GitHub is connected:

1. Open the Codex or ChatGPT review settings for GitHub.
2. Enable code review for this repository.
3. If you want background review on every PR, enable automatic reviews.
4. If you only want on-demand review, keep automatic reviews off and use PR comments instead.

OpenAI's current help guidance says Codex can:

- automatically review code directly in GitHub
- automatically review personal pull requests
- support team-level automatic reviews for repositories

## How To Use It On Pull Requests

### On-Demand Review

Use a PR comment such as:

```text
@codex review
```

### On-Demand Background Task

Use a PR comment such as:

```text
@codex fix the CI failures
```

or another bounded repository task.

### Automatic Review

If automatic reviews are enabled in the product UI, Codex should begin reviewing matching PRs without a manual comment.

## What To Expect

- Cloud review is best for review, summaries, and bounded follow-up tasks
- local build, ROS validation, fixture regression, and runner-bound report generation still belong on the trusted self-hosted runner
- this repository deliberately does not use `openai/codex-action@v1` as the current activation path

## Recommended Activation Order

1. connect GitHub in ChatGPT or Codex
2. enable review or automatic reviews
3. open a small PR
4. trigger `@codex review`
5. confirm the review behavior before enabling broader automatic review coverage

## If Something Does Not Show Up

- confirm the repo is visible to the GitHub account you connected
- confirm the product-side GitHub integration was authorized successfully
- confirm the review feature is enabled for the repository, not just the account
- use the trusted runner workflows separately; Cloud review and local runner execution are complementary, not the same feature
