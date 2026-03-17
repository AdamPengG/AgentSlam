# Phase 1 Front Stereo NumPy Pad Root Cause

## Summary

The intermittent GS4 front-stereo producer failures were traced to a Python exception in the GS4 Isaac worker, not just to opaque Isaac runtime flake.

The failing exception observed during triage was:

```text
ValueError("unsupported keyword arguments for mode 'edge': {'constant_values'}")
```

## Root Cause

`/home/peng/GS4/sim_gs4_master/scripts/live_isaac_worker.py` padded three lidar-side arrays inside `_read_fastlivo_lidar_snapshot(...)` using `np.pad(..., mode="edge", constant_values=...)`.

That is invalid NumPy usage:

- `constant_values=...` is accepted with `mode="constant"`
- `constant_values=...` is not accepted with `mode="edge"`

When the lidar-side arrays were shorter than the point count and the code took the `mode="edge"` branch, the worker raised the ValueError above and exited during readiness.

## Fix

The padding logic was corrected so that:

- `mode="edge"` is used without `constant_values`
- `mode="constant"` keeps the explicit fallback fill value only for truly empty arrays

The worker was also instrumented to write `runtime/isaac_exit_summary.json` on shutdown so future exits are easier to classify.

## Validation

After the fix:

```bash
START_ATTEMPTS=1 bash /home/peng/AgentSlam/scripts/run_phase1_front_stereo_producer.sh
```

Observed result:

- PASS
- producer reported `front-stereo producer is running`
- foundation contract passed with both `rgb.png` and `rgb_right.png`

Then:

```bash
AUTO_START_PRODUCER=0 bash /home/peng/AgentSlam/scripts/run_phase1_vslam_live_stereo_smoke.sh
```

Observed result:

- PASS
- `visual_slam_node` initialized successfully
- localization runtime reported `active_source = primary`

Current runtime evidence:

- `/home/peng/AgentSlam/artifacts/phase1/office_nova_vslam_live_localization_runtime.json`
- `/home/peng/AgentSlam/artifacts/phase1/logs/front_stereo_producer/foundation_check.txt`

## Remaining Risk

This fixes one concrete crash path and restores the producer plus VSLAM smoke flow, but it does not prove infinite repeated-run stability under all Isaac runtime conditions. The producer retry plus health-gate path should remain in place.
