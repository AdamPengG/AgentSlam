# OpenClaw Path Discovery

## Baseline

- `/home/peng/AgentSlam`: exists, directory, mode `775`
- `/home/peng/AgentSlam/refs`: exists, directory, mode `775`
- `/home/peng/GS4`: exists, directory, mode `775`
- `/home/peng/IsaacSim`: exists, directory, mode `775`
- `/home/peng/isaacsim_assets`: exists, directory, mode `775`
- `/home/peng/.openclaw`: exists, directory, mode `700`
- `/home/peng/.codex`: exists, directory, mode `775`

## Writable scope for this workstream

- repo source and reports under `/home/peng/AgentSlam`
- live OpenClaw state under `~/.openclaw`
- Codex local auth/config under `~/.codex`

## Read-only references

- `/home/peng/GS4`
- `/home/peng/IsaacSim`
- `/home/peng/isaacsim_assets`
- `/home/peng/AgentSlam/refs/*`

## Result

The required baseline paths exist. No path remapping was needed during this
bootstrap pass.
