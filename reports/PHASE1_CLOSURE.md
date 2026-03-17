# Phase 1 Closure

## Completed

- kept the offline fixture baseline and revalidated it with `scripts/run_phase1_fixture.sh`
- upgraded `semantic_mapper_pkg` from fixture-only logic to a node that supports `fixture`, `bag_replay`, and `live_isaac` modes
- added a ROS replay publisher in `sim_bridge_pkg` using standard ROS messages plus a JSON detection envelope on `std_msgs/msg/String`
- froze the preferred Isaac runtime pair to the release launcher and release Python entrypoint
- validated `office.usd` plus `nova_carter.usd` headlessly
- added replay, bridge smoke, and top-level office demo scripts
- built the active Phase 1 ROS workspace packages successfully

## Demo-Ready

- `scripts/run_phase1_fixture.sh`
  - offline regression baseline
- `scripts/run_phase0_bridge_smoke.sh`
  - replay-backed ROS topic contract smoke
- `scripts/run_phase1_replay_demo.sh`
  - rosbag record plus play into the mapper
- `scripts/run_phase1_office_demo.sh`
  - top-level Prompt 4 demo entry

## Not Completed But Not Blocking Review

- no live Isaac ROS bridge was validated in this prompt
- TF and `/clock` are still reserved bridge targets rather than replay acceptance evidence
- replay synchronization is intentionally lightweight and does not yet use `message_filters`

## Next Stage Recommendation

- wire a real Office + Nova Isaac ROS graph that publishes the same topic family as the replay harness
- add TF and `/clock` once the live bridge exists
- keep fixture and replay scripts as regression gates while live bring-up matures
