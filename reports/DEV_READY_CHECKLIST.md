# Development Ready Checklist

## Repository And Config

- project root is `/home/peng/AgentSlam`
- `.codex/config.toml` exists
- agent role files exist
- `AGENTS.md` exists
- `refs/` is ignored

## Environment

- requested shell tools are present according to `reports/ENV_AUDIT.md`
- Isaac install hint exists
- Isaac asset root exists
- office scene candidates are documented
- Nova or fallback wheeled robot candidates are documented

## Documentation

- plans, interfaces, dataflow, and evaluation docs are current
- blockers are recorded
- smoke and acceptance checklists are current
- upstream research planning docs are current

## Manual Actions If Needed

- trust the project in Codex CLI
- enable Multi-agents with `/experimental` if the CLI is not loading project roles
- choose one authoritative Isaac launcher plus Python path before live bring-up

## Ready For

- Prompt 3 clone and indexing work
- Prompt 4 workspace and bridge skeleton work after upstream analysis
