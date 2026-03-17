# Phase 0 Gaps

## Remaining Gaps

- no real Isaac GUI session has yet published ROS topics directly into `semantic_mapper_pkg`
- TF and `/clock` are still part of the documented bridge target rather than the replay-backed acceptance evidence
- manual operators still need to remember to use `/usr/bin/python3` for ROS nodes because the active conda Python does not load `rclpy`

## Why These Gaps Do Not Block Phase 1

- the Prompt 4 acceptance route requires at least one real ROS chain, and the replay path now satisfies that requirement
- the release launcher, office stage, and Nova Carter asset were validated directly, so the remaining live gap is isolated to ROS bridge wiring
- the offline fixture baseline remains available as a regression harness while the live bridge is refined
