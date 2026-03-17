# OpenClaw ACP Status

## Current live runtime

- ACPX runtime plugin is loaded in the live gateway
- gateway logs show `acpx runtime backend ready`
- live default model is now `codex-cli/gpt-5.3-codex`
- heavy coding and evaluation agents retain `codex-cli/gpt-5.4`

## ACP plugin baseline

- bundled plugin `acpx` exists in the installed OpenClaw distribution
- current live plugin state: `acpx` is enabled, loaded, and ready

## Codex side readiness

- `codex login status`: `Logged in using ChatGPT`
- repo `.codex/config.toml` already declares the GitNexus MCP server and the `ops_dev` role

## Current conclusion

- live mode today is **ACPX-enabled Codex control plane working**
- planner/reporter default to the lighter coding model
- coder/evaluator keep the heavier model for real implementation and validation
