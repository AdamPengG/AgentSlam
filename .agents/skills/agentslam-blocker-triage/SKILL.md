# agentslam-blocker-triage

Use when a failure or stall needs a bounded diagnosis and the next smallest
action.

## Categories

- environment
- dependency
- data
- upstream interface
- own code
- OpenClaw config
- Telegram
- GPU
- Isaac

## Workflow

1. inspect the failing log or report
2. classify the failure into one primary bucket
3. propose the next smallest safe action
4. record the result in `reports/triage/` or `reports/openclaw/`
