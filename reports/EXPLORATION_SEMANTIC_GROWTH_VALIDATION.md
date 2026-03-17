# Exploration-Backed Semantic Growth Validation

## Scope

Validate the new Phase 1 offline exploration scaffold that orders candidate viewpoints, fuses each visited frame
through `SemanticMapBuilder`, and exports both a final semantic map and per-step progress evidence.

## GitNexus Note

- `gitnexus_query` and `gitnexus_context` were used during code understanding for the semantic mapper call surface.
- `gitnexus_impact` was attempted before the earlier symbol edits, but the MCP transport returned `Transport closed`.
- Local caller scans were used as the fallback scope check for `SemanticMapBuilder` and `run_query_main`.

## Commands Run

### Build

```bash
set +u
source /opt/ros/humble/setup.bash
set -u
cd /home/peng/AgentSlam/ros_ws
colcon build --packages-select semantic_mapper_pkg nav2_overlay_pkg
```

### Focused Unit Tests

```bash
PYTHONPATH=/home/peng/AgentSlam/ros_ws/src/semantic_mapper_pkg:/home/peng/AgentSlam/ros_ws/src/nav2_overlay_pkg \
/usr/bin/python3 -m unittest \
  ros_ws.src.nav2_overlay_pkg.test.test_exploration_demo \
  ros_ws.src.semantic_mapper_pkg.test.test_semantic_mapper \
  ros_ws.src.semantic_mapper_pkg.test.test_runtime_contract
```

### Exploration Demo

```bash
bash /home/peng/AgentSlam/scripts/run_phase1_exploration_demo.sh
```

## Results

- package build: PASS
- focused unit tests: PASS
- offline exploration demo: PASS

## Key Observations

- the greedy route visits four viewpoints and increases semantic coverage before revisiting redundant observations
- the final exported map contains six semantic objects across six labels
- repeated observations for `chair` and `cabinet` are merged into single objects with `observation_count = 2`
- the progress artifact shows when new labels stop appearing, which is a useful bridge toward future exploration stopping logic

## Evidence

- exploration fixture:
  - `fixtures/semantic_mapping/exploration_gt_pose_scene.json`
- exploration map:
  - `artifacts/phase1/exploration_semantic_map.json`
- exploration progress:
  - `artifacts/phase1/exploration_progress.json`
- exploration query outputs:
  - `artifacts/phase1/exploration_queries/query_chair.json`
  - `artifacts/phase1/exploration_queries/query_cabinet.json`
  - `artifacts/phase1/exploration_queries/query_sofa.json`

## Current Limits

- this is an offline artifact-backed scaffold, not a live Nav2 exploration loop
- viewpoint selection uses a simple greedy heuristic instead of frontier coverage or room-aware planning
- localization still depends on GT pose, consistent with the current Phase 1 project boundary
