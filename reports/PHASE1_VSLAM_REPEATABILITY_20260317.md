# Phase 1 Live Stereo VSLAM Repeatability

## Goal

Check whether the repaired front-stereo producer and live stereo VSLAM smoke can pass repeatedly from a clean start.

## Command Pattern

Each run used the existing end-to-end smoke entrypoint:

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_vslam_live_stereo_smoke.sh
```

The runs were executed sequentially from a clean producer state, and each run copied its runtime plus log artifacts into:

- `/home/peng/AgentSlam/artifacts/phase1/repeatability/20260317-153437`

## Results

- run 1: PASS
  - start: `2026-03-17T15:34:37+08:00`
  - end: `2026-03-17T15:36:02+08:00`
  - `active_source=primary`
  - `primary_messages=40`
  - `fallback_messages=0`
  - `published_messages=87`
- run 2: PASS
  - start: `2026-03-17T15:36:04+08:00`
  - end: `2026-03-17T15:37:29+08:00`
  - `active_source=primary`
  - `primary_messages=31`
  - `fallback_messages=0`
  - `published_messages=79`
- run 3: PASS
  - start: `2026-03-17T15:37:31+08:00`
  - end: `2026-03-17T15:38:57+08:00`
  - `active_source=primary`
  - `primary_messages=33`
  - `fallback_messages=0`
  - `published_messages=81`

## Operational Observations

- no run fell back to GT odometry
- no run left lingering producer, bridge, or VSLAM processes after completion
- the repaired GS4 worker plus the AgentSlam retry and health-gate path are now strong enough to survive repeated on-demand bring-up in this session

## Evidence

- repeatability bundle:
  - `/home/peng/AgentSlam/artifacts/phase1/repeatability/20260317-153437`
- per-run runtime summaries:
  - `/home/peng/AgentSlam/artifacts/phase1/repeatability/20260317-153437/run1/office_nova_vslam_live_localization_runtime.json`
  - `/home/peng/AgentSlam/artifacts/phase1/repeatability/20260317-153437/run2/office_nova_vslam_live_localization_runtime.json`
  - `/home/peng/AgentSlam/artifacts/phase1/repeatability/20260317-153437/run3/office_nova_vslam_live_localization_runtime.json`

## Conclusion

For this machine and this workspace state, the live stereo VSLAM path cleared three consecutive clean reruns. That is strong enough to treat the current implementation as ready to checkpoint into git, while still keeping the retry plus health-gate orchestration in place as a guardrail.
