# Isaac Discovery

## Purpose

Prompt 1 must not guess the Isaac Sim install path. This report records the lightweight discovery steps that were run and the current status.

## Discovery Steps Run

1. searched `/home/peng` up to depth 2 for directories or symlinks containing `isaac` or `omniverse`
2. checked whether `isaac-sim.sh`, `isaacsim`, or `omniverse-launcher` are available on `PATH`
3. checked that the fixed asset root `/home/peng/isaacsim_assets` exists and has visible subdirectories

## Findings

- candidate install directory found: `/home/peng/IsaacSim`
- asset root exists: `/home/peng/isaacsim_assets`
- visible asset subtree: `/home/peng/isaacsim_assets/Assets/Isaac`
- no Isaac launcher command was found on `PATH` during this run

## Current Conclusion

The asset root appears usable, but the executable install path is still unconfirmed. This does not block Prompt 1 bootstrap work, but it remains an environment discovery item for Prompt 2.
