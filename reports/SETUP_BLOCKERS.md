# Setup Blockers

## Active Items

### B-002: Codex CLI trust and multi-agent toggle require manual confirmation

- status: manual-check
- impact: project-level `.codex/config.toml` and agent roles may not load in Codex CLI unless the project is trusted and Multi-agents is enabled
- evidence: shell access can verify files exist, but cannot prove current Codex CLI trust state
- mitigation: in Codex CLI, mark the project as trusted and enable Multi-agents with `/experimental` if needed, then restart Codex
- blocking level: does not block shell-side execution

### B-004: Live Isaac ROS topic bridge is still not a validated acceptance path

- status: open
- impact: Prompt 4 closes Phase 1 with a replay-backed ROS chain, but not with a real Isaac GUI or live bridge publishing ROS topics into the mapper
- evidence:
  - `scripts/run_isaac_office_nova.sh` validates `office.usd` plus `nova_carter.usd` headlessly
  - `scripts/run_phase0_bridge_smoke.sh` validates the topic contract through the replay publisher
  - no command in this prompt produced a live Isaac ROS2 image or IMU stream from the simulator itself
- mitigation:
  - use `IsaacSim-ros_workspaces` plus the validated release launcher pair to wire a real Office + Nova ROS graph
  - preserve the replay path as the fallback regression harness
- blocking level: does not block Phase 1 review, but blocks claiming a live Isaac ROS demo

### B-005: ROS runtime must use system Python, not the active conda Python

- status: open
- impact: ROS2 `rclpy` nodes fail if launched with the current conda `python3`
- evidence:
  - `/usr/bin/python3` imports `rclpy` successfully after sourcing ROS
  - conda `python3` previously failed on `rclpy._rclpy_pybind11`
- mitigation:
  - all Prompt 4 ROS scripts now use `/usr/bin/python3`
  - keep `set +u; source /opt/ros/humble/setup.bash; set -u` in rerunnable shell scripts
- blocking level: not blocking the current scripts, but important for manual operator runs

### B-006: Codex Cloud and GitHub review features still require manual product-side activation

- status: manual-check
- impact: the repository can provide workflows and runbooks, but cannot by itself connect ChatGPT or Codex to GitHub or enable automatic reviews
- evidence:
  - Prompt 5 can only add local docs, prompts, scripts, and workflow YAML
  - Cloud review activation lives in ChatGPT or Codex settings plus GitHub authorization
- mitigation:
  - follow `docs/CODEX_CLOUD_GITHUB_SETUP.md`
  - verify `@codex review` on a small PR after connecting GitHub
- blocking level: does not block local runner automation, but blocks actual Cloud review usage until completed

### B-007: Self-hosted GitHub runner is not registered yet

- status: manual-check
- impact: workflow YAML can be prepared locally, but scheduled and dispatchable jobs will remain queued until a matching runner is registered and online
- evidence:
  - Prompt 5 adds workflows expecting labels such as `self-hosted`, `linux`, `agentslam`
  - no repository-side change can register a runner token or install the service automatically
- mitigation:
  - follow `docs/SELF_HOSTED_RUNNER_SETUP.md`
  - bootstrap a safe scaffold with `scripts/ops/bootstrap_self_hosted_runner.sh`
  - register the runner in GitHub and verify the labels
- blocking level: blocks GitHub-side execution, but not local shell validation

### B-008: Full Codex-generated nightly summary and handoff are now bounded by precomputed delta plus fallback reports

- status: resolved
- impact: the nightly suite no longer depends on a wide, slow Codex read path to produce operator-visible summary and handoff files
- evidence:
  - `bash scripts/ops/nightly_phase1_eval.sh` completed successfully for timestamp `20260316-222035`
  - `reports/nightly/nightly_phase1_eval_20260316-222035.md` and `reports/nightly/nightly_handoff_20260316-222035.md` were both written
  - `artifacts/nightly/20260316-222035/nightly_delta.md` precomputed the cross-nightly comparisons before Codex summarization
  - `artifacts/nightly/20260316-222035/codex/nightly_phase1_eval/nightly_phase1_eval_meta.txt` shows the bounded summary task completed with status `0`
- mitigation:
  - keep the shell fallback plus Codex overwrite design
  - keep the summary prompt scoped to the precomputed delta unless a suite stage fails
- blocking level: no longer blocking Prompt 5 nightly closure

### B-009: Preferred VSLAM backend depends on an external overlay instead of an AgentSlam-owned workspace

- status: open
- impact: AgentSlam can now source a real `isaac_ros_visual_slam` backend from `/home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash`, but the dependency is still external and live Isaac Office + Nova input is not yet the validated source
- evidence:
  - `ros2 pkg prefix isaac_ros_visual_slam` succeeds after sourcing `/home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash`
  - `ros_ws/launch/phase1_vslam_stereo.launch.py` now defines the AgentSlam stereo VSLAM bring-up contract
  - `artifacts/phase1/office_nova_localization_runtime.json` still shows the replay-backed localized demo using fallback odometry
- mitigation:
  - keep `/agentslam/localization/odom` as the stable consumer-facing topic while sourcing the external overlay for smoke and early bring-up
  - move the VSLAM dependency into an AgentSlam-owned workspace or document it as a formal external prerequisite
  - validate the live Isaac Office + Nova front-stereo topic stream as the acceptance source
- blocking level: does not block VSLAM smoke validation, but blocks claiming a self-contained or live Isaac VSLAM localization stack

### B-010: GS4 Isaac front-stereo runtime is intermittently unstable across reruns

- status: resolved
- impact: the previously flaky live front-stereo bring-up path is repaired for the current workspace state; the retry plus health-gate orchestration stays in place as an operational guardrail
- evidence:
  - successful live stereo VSLAM smoke snapshot:
    - `artifacts/phase1/success/20260317-135853`
    - `artifacts/phase1/success/20260317-143724`
  - successful smoke handoff:
    - `reports/PHASE1_VSLAM_STEREO_SMOKE_AUTOSTART.md`
    - `reports/PHASE1_FRONT_STEREO_STABILITY_HARDENING.md`
  - latest strict producer rerun:
    - an initial strict rerun failed after `5` attempts on `2026-03-17` and surfaced a concrete GS4 worker crash via the new exit-summary artifact
    - the crash was traced to invalid NumPy padding logic in `/home/peng/GS4/sim_gs4_master/scripts/live_isaac_worker.py`
    - after the fix, `START_ATTEMPTS=1 bash scripts/run_phase1_front_stereo_producer.sh` passed
    - `AUTO_START_PRODUCER=0 bash scripts/run_phase1_vslam_live_stereo_smoke.sh` passed with `active_source=primary`
    - three consecutive clean smoke reruns passed under `artifacts/phase1/repeatability/20260317-153437`
  - intermittent failure modes:
    - before the fix, `artifacts/phase1/logs/front_stereo_producer/foundation_check.txt` could fail because `runtime/live_frames/rgb.png` and `rgb_right.png` never arrived before the worker exited
    - the concrete crash root cause and fix are documented in `reports/triage/PHASE1_FRONT_STEREO_NUMPY_PAD_ROOT_CAUSE.md`
- mitigation:
  - keep the new producer retry plus health-gate path because it now fails fast instead of stalling on dead workers
  - keep the autostart smoke as the acceptance entrypoint because it refuses to launch VSLAM on incomplete stereo runtime state
  - keep the new `isaac_exit_summary.json` artifact enabled so any future regressions leave a concise failure signature
  - continue watching for any remaining causes of premature worker exit now that the NumPy padding crash is fixed
- blocking level: no longer blocking current live front-stereo VSLAM acceptance

## Resolved Items

- B-001: preferred Isaac launcher and Python pair are now frozen to the release paths and validated headlessly
- B-003: all required refs are now cloned or refreshed successfully
