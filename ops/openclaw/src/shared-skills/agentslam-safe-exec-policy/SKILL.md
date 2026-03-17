# agentslam-safe-exec-policy

Shared OpenClaw skill mirror.

- Prefer `reports/openclaw/CURRENT_STATE.md` over re-reading many long docs.
- Prefer wrapper scripts over free-form shell.
- Let shell or scripts extract deltas before asking an LLM to summarize them.
- Keep routine planner and reporter work on lighter models.
- Never write to read-only reference trees.
- Avoid broad home-directory scans.
