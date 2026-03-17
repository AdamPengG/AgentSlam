# AgentSlam Evaluation Draft

## Evaluation Philosophy

Each phase should end with evidence, not assumptions. Reports under `reports/` are the contract surface for whether a phase is actually ready to advance.

## Phase 0 Acceptance

Phase 0 is acceptable when all of the following are true:

- Prompt 1 bootstrap files remain valid
- Prompt 2 scripts exist and are executable
- environment audit is captured in `reports/ENV_AUDIT.md`
- Isaac discovery is captured in `reports/ISAAC_DISCOVERY.md`
- upstream research planning docs exist
- tester checklists exist for smoke, acceptance, clone and index, and development readiness
- known blockers are documented without stopping unrelated work

## Phase 0 Current Status

- shell-level tooling audit: available for all requested tools
- Isaac launcher and Python pair: frozen to the release paths and validated
- office scene and Nova robot pair: validated headlessly
- refs clone and GitNexus indexing: complete enough for Prompt 4 closure

## Phase 1 Current Status

- offline semantic mapping fixture: implemented and validated
- semantic query layer: label and spatial-filter query coverage is part of the baseline
- offline exploration-backed semantic map growth: implemented and validated
- localization adapter plus localized geometric map export: implemented and validated
- unit tests for projection, runtime contract, and fixture loading: passing
- ROS workspace build: passing
- replay-backed ROS topic chain into the mapper: passing
- normalized localization-backed semantic and geometric mapping chain: passing
- stereo `isaac_ros_visual_slam` launch surface and idle smoke through the normalized localization contract: passing
- full live stereo `isaac_ros_visual_slam` smoke through the normalized localization contract: pending a live front-stereo producer on this host
- live Isaac bring-up: still outside the acceptance gate for this run

## Phase 1 Acceptance Preview

Minimum runtime acceptance should include:

- one build or package-level validation pass
- one smoke startup check confirming image, camera info, IMU, GT pose, and detection transport
- one validation pass confirming `/agentslam/localization/odom` can drive both geometric and semantic mapping outputs
- one validation pass confirming `/agentslam/localization/odom` can switch to a real VSLAM primary source without changing downstream topic names
- explicit confirmation that LiDAR is not part of the baseline contract
- one replay or static validation pass
- one artifact-backed validation pass showing map growth across more than one viewpoint
- documentation of exact commands, expected topics, and failure modes

## Phase 1 Acceptance Result

- build: PASS
- bridge smoke: PASS
- replay demo: PASS
- localized mapping demo: PASS
- operator office demo: PASS
- live Isaac ROS bridge: not yet required for this phase, therefore not a failure

## Candidate Metrics

- the chosen Isaac launcher starts reproducibly
- the selected office scene and wheeled robot pair are documented
- camera and IMU streams appear with plausible metadata
- GT pose is aligned well enough for early evaluation and semantic skeleton work
- the first semantic outputs can be produced without inventing custom messages
- the localization contract is stable enough that GT fallback can later be replaced by VSLAM without changing mapper outputs
- the preferred VSLAM backend should be validated through the same `/agentslam/localization/odom` contract before any live Isaac semantic acceptance claims

## Decision Gates Before Phase 2

- keep the replay path as a regression harness
- add a real live Isaac ROS publisher that matches the current topic contract
- complete the live Isaac Office + Nova front-stereo VSLAM smoke
- decide whether TF and `/clock` become hard acceptance requirements

## Prompt 5 Ops Acceptance

Prompt 5 is acceptable when all of the following are true:

- `scripts/ops/check_codex_auth.sh` reports clear pass/fail state without mutating auth
- `scripts/ops/with_codex_lock.sh` serializes `codex exec`
- a repeatable Phase 1 suite script writes both a report and captured artifacts
- nightly, plan-refresh, and triage prompt files exist under `prompts/exec/`
- workflows exist for CI, nightly eval, plan refresh, and triage
- owner-facing docs exist for Cloud setup, runner setup, auth, and operations
- at least one local `codex exec` smoke run writes a report under `reports/`

## Prompt 5 Evidence Locations

- ops architecture and runbooks: `docs/`
- exec prompts: `prompts/exec/`
- ops scripts: `scripts/ops/`
- nightly reports: `reports/nightly/`
- plan refresh reports: `reports/plan_refresh/`
- triage reports: `reports/triage/`
- nightly and exec artifacts: `artifacts/nightly/`, `artifacts/ops/`

## OpenClaw Control Plane Acceptance

The OpenClaw bootstrap layer is acceptable when all of the following are true:

- repo-side source exists under `ops/openclaw/`
- validation passes through `ops/openclaw/bin/validate_openclaw.sh`
- a backup-first dry-run deploy is demonstrated
- baseline reports exist for path discovery, security, ACP, Telegram, cron, and skills
- no live cutover happens without an explicit checklist and rollback path

## OpenClaw Evidence Locations

- source and scripts: `ops/openclaw/`
- reports: `reports/openclaw/`
- machine state after deployment: `~/.openclaw/`

## Evidence Locations

- environment, discovery, and validation: `reports/`
- planning and contracts: `docs/`
- future runtime artifacts: `maps/`, `bags/`, and `ros_ws/`
