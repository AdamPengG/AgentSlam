# OpenClaw Token Efficiency Mode

## Goal

Reduce routine token waste without crippling the usefulness of the AgentSlam
control plane.

## Changes Applied

1. model layering
   - default planner-style work now prefers `codex-cli/gpt-5.3-codex`
   - coder and evaluator keep `codex-cli/gpt-5.4`
   - reporter also defaults to `codex-cli/gpt-5.3-codex`
2. lower concurrency
   - agent concurrency reduced to 1
   - subagent concurrency reduced to 1
3. shorter session lifetime
   - global idle reset reduced to 120 minutes
   - direct-session idle reset reduced to 90 minutes
   - group idle reset reduced to 30 minutes
4. shorter cron memory tail
   - cron session retention reduced from 24h to 6h
   - cron log retention reduced
5. compact state briefing added
   - `reports/openclaw/CURRENT_STATE.md`
6. workspace instructions updated
   - read compact state before larger reports
   - keep heartbeat lightweight
7. skills updated
   - orchestrator and safe-exec policy now explicitly prefer compact state and
     shell-first delta extraction

## Expected Effect

- fewer heavy-model invocations for routine planning and reporting
- less stale conversational baggage carried into background work
- lower risk of parallel background tasks multiplying token use
- lower chance that OpenClaw rereads the same large docs every cycle

## Notes

- This does not eliminate token usage from real coding, testing, or replay
  evaluation. Those remain intentionally heavier.
- If future cron jobs are added, they should stay event-driven and wrapper-led.
