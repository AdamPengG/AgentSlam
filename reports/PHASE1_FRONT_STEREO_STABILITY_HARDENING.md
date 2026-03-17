# Phase 1 Front Stereo Stability Hardening

## Goal

Reduce the operator-facing flake rate of the GS4 front-stereo producer without changing the VSLAM contract itself.

## Changes

- `scripts/run_phase1_front_stereo_producer.sh`
  - retries cold start up to 5 attempts by default
  - requires the GS4 foundation contract to pass before declaring the producer ready
  - keeps message-based stereo readiness checks
  - now aborts readiness waits immediately if the Isaac worker or stereo bridge exits mid-check
  - requires the worker plus bridge to stay alive for a short post-readiness health window before reporting success
  - now prints whether a failed attempt died during readiness or after readiness but before the short health window completed
  - now cleans up worker and bridge process groups instead of only the wrapper pid
  - escalates cleanup between failed attempts so a bad Isaac cold start does not poison the next attempt
  - disowns successful background jobs so the producer bootstrap shell can exit cleanly
- `scripts/run_phase1_vslam_live_stereo_smoke.sh`
  - exposes `PRODUCER_START_ATTEMPTS` so the end-to-end smoke can tolerate intermittent producer cold-start failures
  - keeps the end-to-end odometry capture as the final acceptance gate
- `scripts/stop_phase1_front_stereo_producer.sh`
  - now uses staged INT/TERM/KILL shutdown instead of a single interrupt
  - now targets the worker and bridge process groups so Isaac child processes do not linger after stop
- `scripts/wait_for_stereo_runtime.py`
  - supports optional frame-progress diagnostics for future triage, but the default acceptance path stays grounded in foundation-contract success and final odometry capture
- `/home/peng/GS4/sim_gs4_master/scripts/live_isaac_worker.py`
  - writes `runtime/isaac_exit_summary.json` on shutdown so producer failures leave a concise classification artifact
  - fixes invalid `np.pad(..., mode="edge", constant_values=...)` usage inside `_read_fastlivo_lidar_snapshot(...)`

## What Happened In Practice

During the hardening run, the new bootstrap logic caught bad starts instead of handing them to VSLAM:

- one rerun failed because the stereo producer never became materially ready
- another rerun reached stereo metadata but stalled before becoming a reliable acceptance candidate
- the final rerun recovered and the full live stereo VSLAM smoke passed

This is the behavior we want from the orchestration layer:

- reject incomplete stereo runtime states early
- retry cleanly
- only continue once the real end-to-end smoke succeeds

## Validation

### End-to-End Smoke

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_vslam_live_stereo_smoke.sh
```

Observed result:

- PASS
- the smoke auto-started the GS4 front-stereo producer after live stereo topics were absent
- the producer cold-start path retried until the GS4 foundation contract passed
- `isaac_ros_visual_slam` initialized successfully
- `/visual_slam/tracking/odometry` was captured
- `/agentslam/localization/odom` was captured
- `/agentslam/localization/status` reported `active_source=primary`

Latest validated runtime summary:

- `primary_messages = 82`
- `fallback_messages = 0`
- `published_messages = 142`
- `active_source = primary`

### Producer Lifecycle Check

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_front_stereo_producer.sh
bash /home/peng/AgentSlam/scripts/stop_phase1_front_stereo_producer.sh
```

Observed result:

- PASS after root-cause fix
- earlier strict revalidation exposed a real GS4 worker crash instead of leaving the producer hung in readiness
- the new `isaac_exit_summary.json` artifact revealed a concrete Python exception in `_read_fastlivo_lidar_snapshot(...)`
- after fixing that crash path, `START_ATTEMPTS=1 bash /home/peng/AgentSlam/scripts/run_phase1_front_stereo_producer.sh` now reports readiness successfully
- `bash /home/peng/AgentSlam/scripts/stop_phase1_front_stereo_producer.sh` now shuts the worker and bridge down without leaving lingering long-lived processes behind

### Latest Strict Revalidation

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_front_stereo_producer.sh
```

Observed result:

- first strict revalidation failed after `5` attempts and exposed the concrete GS4 worker crash path
- after the GS4 fix, the same strict revalidation passed with `START_ATTEMPTS=1`
- the bootstrap shell now either reports readiness or fails fast with actionable stderr instead of silently parking on a stale readiness helper

## Evidence

- latest validated rerun snapshot:
  - `artifacts/phase1/success/20260317-143724`
- raw VSLAM odometry:
  - `artifacts/phase1/success/20260317-143724/office_nova_vslam_live_raw_odom.txt`
- normalized localization odometry:
  - `artifacts/phase1/success/20260317-143724/office_nova_vslam_live_localization_odom.txt`
- localization runtime:
  - `artifacts/phase1/success/20260317-143724/office_nova_vslam_live_localization_runtime.json`
- localization status:
  - `artifacts/phase1/success/20260317-143724/office_nova_vslam_live_status.txt`
- VSLAM launch log:
  - `artifacts/phase1/success/20260317-143724/phase1_vslam_live_stereo_launch.log`
- localization adapter log:
  - `artifacts/phase1/success/20260317-143724/phase1_vslam_live_stereo_localization.log`
- current GS4 worker and bridge logs:
  - `artifacts/phase1/success/20260317-143724/live_isaac_worker.log`
  - `artifacts/phase1/success/20260317-143724/stereo_bridge.log`
  - `artifacts/phase1/success/20260317-143724/foundation_check.txt`
- latest strict-revalidation logs:
  - `artifacts/phase1/logs/front_stereo_producer/live_isaac_worker.log`
  - `artifacts/phase1/logs/front_stereo_producer/stereo_bridge.log`
  - `artifacts/phase1/logs/front_stereo_producer/foundation_check.txt`
- root-cause report:
  - `reports/triage/PHASE1_FRONT_STEREO_NUMPY_PAD_ROOT_CAUSE.md`

## Remaining Risk

The upstream GS4 Isaac worker is still the real source of flake. AgentSlam now handles that flake more honestly and more usefully, but it does not eliminate the underlying simulator/runtime instability:

- bad starts can still happen
- the difference is that the bootstrap path now retries instead of blindly passing a half-ready producer downstream

## Conclusion

- the double-eye production chain is in a much healthier state now because one concrete GS4 crash path has been removed
- the AgentSlam side is now safer to operate because bad starts are rejected quickly and cleaned up completely
- we have both prior successful live stereo VSLAM evidence and a new post-fix strict producer rerun that succeeds again
- repeated-run stability is improved, but it is still worth keeping the retry plus health-gate path in place
