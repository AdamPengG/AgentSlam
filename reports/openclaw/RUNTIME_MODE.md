# OpenClaw Runtime Mode

## Live mode now

- mode: `acpx-ready Codex control plane`
- gateway default model: `codex-cli/gpt-5.3-codex`
- heavy-work agents:
  - `coder -> codex-cli/gpt-5.4`
  - `evaluator -> codex-cli/gpt-5.4`
- light-work agents:
  - `planner -> codex-cli/gpt-5.3-codex`
  - `reporter -> codex-cli/gpt-5.3-codex`
- status: working

## Repo-side target mode

- mode: `acpx preferred`
- fallback: `codex-cli/gpt-5.4`
- rollout posture: deployed and validated locally

## Interpretation

This machine is now running the repo-managed control-plane baseline with ACPX
loaded, Telegram active, and model layering tuned for lower routine token use.
The remaining work is operational refinement, not initial cutover.
