## GitNexus MCP Repair - 2026-03-17

### Summary

GitNexus CLI and repository index are healthy on this machine, but Codex MCP calls were failing with `Transport closed` because the active VS Code Codex extension host was still running an old OpenAI extension build.

### Evidence

- `npx gitnexus --version` returned `1.4.1`.
- `npx gitnexus status` in `/home/peng/AgentSlam` reported the repo as indexed and up to date at commit `a0f5e08`.
- The live Codex log at `/home/peng/.config/Code/logs/20260317T074030/window1/exthost/openai.chatgpt/Codex.log` showed fresh errors at `2026-03-17 18:53` from:
  - `/home/peng/.vscode/extensions/openai.chatgpt-26.311.21342-linux-x64/out/extension.js`
- The running Codex app server process was:
  - `/home/peng/.vscode/extensions/openai.chatgpt-26.311.21342-linux-x64/bin/linux-x86_64/codex app-server --analytics-default-enabled`
- VS Code's installed-extension registry already marked the latest OpenAI extension as:
  - `openai.chatgpt` version `26.313.41514`

### Root Cause

VS Code/Codex had not cleanly reloaded after extension updates, so the live extension host and Codex app server were still bound to the old `26.311.21342` installation. GitNexus MCP failures were a symptom of that stale runtime, not a GitNexus CLI/index failure.

### Repair Performed

The following stale extension directories were disabled by renaming them out of the normal extension search path:

- `/home/peng/.vscode/extensions/openai.chatgpt-26.311.21342-linux-x64`
- `/home/peng/.vscode/extensions/openai.chatgpt-26.313.41036-linux-x64`

They were renamed to:

- `/home/peng/.vscode/extensions/openai.chatgpt-26.311.21342-linux-x64.disabled-20260317-185630`
- `/home/peng/.vscode/extensions/openai.chatgpt-26.313.41036-linux-x64.disabled-20260317-185630`

The only remaining active installation directory is:

- `/home/peng/.vscode/extensions/openai.chatgpt-26.313.41514-linux-x64`

### Remaining Action

A VS Code/Codex reload is still required because the currently running extension host was started before the on-disk cleanup. After reload, Codex should start from the latest extension directory and GitNexus MCP calls can be re-tested.

Recommended reload sequence:

1. Close the current VS Code window for `/home/peng/AgentSlam`.
2. Reopen VS Code in `/home/peng/AgentSlam`.
3. Re-run a lightweight GitNexus MCP call such as `list_repos` or `impact`.

### Safety Notes

- No project source files were changed during this repair.
- No Git operations were performed.

### Final Root Cause After Reload

After VS Code reload, the old extension problem was fixed, but `gitnexus impact` still failed specifically on AgentSlam class symbols.

Confirmed behavior on 2026-03-17:

- `list_repos`, `query`, `context`, and `cypher` worked on AgentSlam.
- `impact` on AgentSlam class symbols such as `LocalizationAdapterNode` and `SemanticMapperNode` crashed with `Segmentation fault (core dumped)` when invoked through the GitNexus CLI.
- `impact` on another indexed repo (`isaac_ros_visual_slam`) worked, which narrowed the failure to the AgentSlam + `impact` path rather than a full GitNexus install failure.

This showed that the remaining failure was a GitNexus 1.4.1 `impact` implementation bug on this repository, not a stale-extension problem.

### Final Repair Performed

Additional recovery steps:

1. Rebuilt the AgentSlam GitNexus index:
   - `npx gitnexus clean -f`
   - `npx gitnexus analyze -f /home/peng/AgentSlam`
2. Patched the local cached GitNexus 1.4.1 package in:
   - `/home/peng/.npm/_npx/5e786f48223a616c/node_modules/gitnexus/dist/mcp/local/local-backend.js`
   - `/home/peng/.npm/_npx/e46929201c1128dd/node_modules/gitnexus/dist/mcp/local/local-backend.js`
3. Replaced the crashing `impact()` implementation with a safer parameterized-query fallback that avoids the segfaulting path.
4. Restarted the live Codex app-server so the MCP layer reloaded the patched local GitNexus code.

Backups of the original cached files were preserved next to the patched files with suffix:

- `.bak-20260317-impact-segfault`

### Validation

The following checks succeeded after the repair:

- `mcp gitnexus/list_repos`
- `mcp gitnexus/query`
- `mcp gitnexus/context`
- `mcp gitnexus/impact`
- `npx gitnexus impact -r AgentSlam LocalizationAdapterNode`
- `npx gitnexus impact -r AgentSlam SemanticMapperNode`

Example recovered MCP result:

- `impact({target: "LocalizationAdapterNode", direction: "upstream", repo: "AgentSlam"})`
  - `impactedCount = 2`
  - `risk = LOW`
  - direct caller: `main`

### Current Status

GitNexus is usable again for AgentSlam in this Codex session, including the previously broken `impact` tool.
