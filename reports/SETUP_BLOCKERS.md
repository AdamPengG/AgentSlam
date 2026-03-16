# Setup Blockers

## Active Items

### B-001: Isaac Sim executable path not yet confirmed

- status: open
- impact: launcher scripts and reproducible run commands cannot be finalized yet
- evidence: `/home/peng/IsaacSim` exists as a candidate install directory, but no Isaac launcher command was found on `PATH`
- mitigation: create and run `scripts/discover_isaac_assets.sh` in Prompt 2 to enumerate launchers, Python entrypoints, office USD candidates, and Nova robot assets
- blocking level: does not block Prompt 1 bootstrap completion
