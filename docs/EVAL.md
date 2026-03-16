# AgentSlam Evaluation Draft

## Evaluation Philosophy

The project should advance through explicit gates instead of “it probably works” assumptions. Each phase needs a small, testable acceptance target with evidence stored under `reports/`.

## Phase 0 Acceptance

Phase 0 is successful when:

- bootstrap files and directory skeleton are present
- git branch and remote are configured
- project-level Codex multi-agent configuration exists
- key planning, interface, dataflow, and evaluation documents exist
- setup status, Git status, Isaac discovery, and blockers are recorded

## Phase 1 Acceptance Preview

Minimum runtime acceptance should include:

- one build of the ROS workspace or equivalent packages
- one smoke startup check covering time, TF, camera, and IMU topics
- one replay or static validation pass
- documentation of exact commands, expected topics, and failure modes

## Candidate Metrics

- bridge startup succeeds without manual patching
- expected visual and IMU topics appear with plausible rates
- GT pose is available and correctly frame-aligned for early evaluation
- the office scene and Nova baseline can be reproduced consistently

## Known Risks

- Isaac Sim executable entrypoint is not yet confirmed on this machine
- upstream package choices are not yet frozen
- semantic map output contracts are still placeholders

## Evidence Locations

- environment and setup: `reports/`
- interface and design records: `docs/`
- local runtime artifacts: `maps/`, `bags/`, and later `ros_ws/`
