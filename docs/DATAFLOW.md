# AgentSlam Dataflow Draft

## Phase 0 Intent

The current dataflow is a planning draft rather than an implemented runtime. Its purpose is to align future bridge, mapping, navigation, and testing work around a shared pipeline.

## Target Early Pipeline

1. Isaac Sim loads an office scene and a Nova wheeled robot.
2. The bridge publishes simulation time, TF, camera images, camera info, IMU, and GT pose.
3. A mapping layer consumes visual plus IMU data and uses GT pose for early alignment and evaluation.
4. Semantic outputs are converted into room-aware structures for downstream planning.
5. A navigation overlay consumes the route graph or semantic map and dispatches goals through standard ROS 2 navigation patterns.
6. Tester flows validate buildability, startup, topic presence, and static or replay-based checks.

## Storage and Artifact Flow

- `maps/base/` will hold baseline map assets or exported geometry references.
- `maps/semantic/` will hold semantic map artifacts.
- `maps/rooms/` will hold room graph or room segmentation outputs.
- `maps/routes/` will hold route graph outputs and related planner artifacts.
- `bags/` will remain ignored and reserved for local runtime capture.
- `reports/` will capture environment audit, smoke checks, validation outcomes, and blockers.

## Coordination Rules

- Bridge, mapping, and navigation work should converge on documented interfaces rather than private assumptions.
- The tester role is responsible for converting runtime assumptions into checklists and pass/fail evidence.
- Upstream analysis should refine this dataflow only after repository references are cloned and inspected.

## Open Questions

- which module owns sensor synchronization
- when semantic map artifacts should be persisted to disk versus served over ROS
- whether route graph generation runs online, offline, or in a hybrid mode during early phases
