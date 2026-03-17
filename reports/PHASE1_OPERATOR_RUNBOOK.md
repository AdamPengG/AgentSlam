# Phase 1 Operator Runbook

## Preconditions

- repository root: `/home/peng/AgentSlam`
- ROS 2 Humble available under `/opt/ros/humble`
- use `/usr/bin/python3` for ROS nodes
- Isaac release install available at `/home/peng/IsaacSim`

## 1. Validate The Isaac Office + Nova Pair

```bash
cd /home/peng/AgentSlam
bash scripts/run_isaac_office_nova.sh --validate-only
```

Expected result:

- `artifacts/phase1/office_nova_isaac_validation.json` is created
- `stage_loaded` is `true`
- `robot_prim_valid` is `true`

## 2. Run The Offline Regression Baseline

```bash
cd /home/peng/AgentSlam
bash scripts/run_phase1_fixture.sh
```

Expected result:

- `artifacts/phase1/synthetic_semantic_map.json`
- `artifacts/phase1/query_chair.json`
- `artifacts/phase1/query_table.json`

## 3. Smoke The Replay Bridge Contract

```bash
cd /home/peng/AgentSlam
bash scripts/run_phase0_bridge_smoke.sh
```

Expected result:

- `artifacts/phase1/phase0_bridge_topics.txt`
- `artifacts/phase1/phase0_bridge_detection_sample.txt`
- `artifacts/phase1/phase0_bridge_odom_sample.txt`

## 4. Run The Replay Demo

```bash
cd /home/peng/AgentSlam
bash scripts/run_phase1_replay_demo.sh
```

Expected result:

- `artifacts/phase1/office_nova_replay_bag`
- `artifacts/phase1/office_nova_replay_semantic_map.json`
- `artifacts/phase1/replay_queries/query_chair.json`
- `artifacts/phase1/replay_queries/query_desk.json`
- `artifacts/phase1/replay_queries/query_cabinet.json`

## 5. Run The Top-Level Office Demo

```bash
cd /home/peng/AgentSlam
bash scripts/run_phase1_office_demo.sh
```

Expected result:

- Isaac validation runs first
- bridge smoke runs next
- replay demo completes and prints artifact paths

## 6. Build The Active Workspace Packages

```bash
cd /home/peng/AgentSlam
set +u
source /opt/ros/humble/setup.bash
set -u
cd ros_ws
colcon build --packages-select sim_bridge_pkg semantic_mapper_pkg room_graph_pkg semantic_query_pkg nav2_overlay_pkg localization_adapter_pkg eval_tools_pkg
```

## Manual Live Attempt

Prompt 4 does not claim a validated live Isaac ROS bridge. The current manual starting point is:

```bash
cd /home/peng/AgentSlam
bash scripts/run_isaac_office_nova.sh --print-live-command
```
