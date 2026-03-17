# Phase 1 VSLAM Path-Following Triage

## Scope

Narrow the localization-quality failure after the new Isaac Sim occupancy-derived start/end benchmark was introduced.

## Benchmark Route

- latest planner probe: `artifacts/phase1/vslam_accuracy/planner_probe_20260317-184913/planned_path.json`
- route mode: `single_goal`
- planned length: `20.002 m`
- planned turn count: `1`
- selection mode: `strict`
- route shape: an initial straight segment followed by a single `-45 deg` turn

## Full Benchmark Result

- full accuracy eval artifact: `artifacts/phase1/vslam_accuracy/20260317-183445`
- report: `reports/PHASE1_VSLAM_ACCURACY_EVAL.md`
- executed reference path length: `6.554 m`
- executed estimate path length: `0.000 m`
- translation RMSE: `5.5615 m`
- yaw RMSE: `65.161 deg`
- localization adapter runtime still showed `active_source=primary`, so the estimate topic was not falling back to GT

## Motion-Mode Probes

### Producer-Only Probe

- native producer with straight `cmd_vel` motion showed `21` unique `/chassis/odom` XY samples over the capture window
- the same run showed `40` unique left-image hashes over `40` image samples
- conclusion: the robot does move and the front stereo stream does change under motion

### Stationary-Then-Move Probe

- VSLAM was started while the robot was stationary, then straight motion was applied
- raw `/visual_slam/tracking/odometry` produced `6` unique XY samples
- normalized `/agentslam/localization/odom` also produced `6` unique XY samples
- conclusion: a stationary startup by itself does not explain the frozen-benchmark failure

### Waypoint-Following Probe

- the same occupancy-derived path was replayed for a short diagnostic run
- `/chassis/odom` produced `250` unique XY samples during the probe
- raw `/visual_slam/tracking/odometry` produced only `7` unique XY samples
- normalized `/agentslam/localization/odom` also produced only `7` unique XY samples
- conclusion: the path-following motion profile causes VSLAM to under-estimate motion severely, even though the robot and cameras continue to move

## Working Conclusion

The current blocker is no longer the benchmark route definition itself.

The latest evidence points to a motion-profile-sensitive VSLAM quality problem:

- the native front-stereo producer is capable of generating changing images during motion
- VSLAM can produce moving odometry on straight-line probes
- the occupancy-derived waypoint-following path causes raw and normalized VSLAM odometry to collapse to a very small trajectory compared with `/chassis/odom`

## Next Debug Targets

- capture raw stereo frames during the waypoint-following benchmark and compare them with the straight-line probe
- reduce follower-induced angular transients and compare VSLAM path growth against the current path
- add IMU to the native producer path and repeat the same benchmark
- keep the occupancy-derived start/end route as the quality gate, but treat straight-line probes as a secondary diagnostic only
