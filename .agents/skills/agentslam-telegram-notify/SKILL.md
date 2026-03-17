# agentslam-telegram-notify

Use for important operator notifications only.

## Trigger

- semantic-map stage completion
- blocking issue that needs human intervention
- explicit operator-facing handoff

## Workflow

1. write or update the backing report first
2. keep the Telegram message short
3. use `bash ops/openclaw/bin/agentslam_notify_telegram.sh`
4. do not send routine progress spam

## Message minimum

- phase or blocker name
- short conclusion
- report path
- smallest next action
