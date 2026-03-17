# Phase 1 VSLAM Accuracy Eval

## Scope

Evaluate AgentSlam's normalized localization output against the native Isaac Sim ROS2 reference odometry on a long Office + Nova Carter route planned from Isaac Sim occupancy data.

## Route Plan

- occupancy-based planned length: `20.002` m
- planned turn count: `1`
- target length: `20.0` m
- path follower completed: `False`
- path follower duration: `180.22` s

## Reference And Estimate

- reference topic: `/chassis/odom`
- estimate topic: `/agentslam/localization/odom`
- duration: `180.0` seconds
- warmup excluded: `3.0` seconds
- matching tolerance: `50.0` ms
- RPE interval: `1.0` seconds
- comparison frame: `each trajectory normalized to its own first matched pose`

## Result

- matched samples: `100`
- reference path length: `2.825` m
- estimate path length: `0.000` m
- translation RMSE: `2.6743` m
- translation mean error: `2.5385` m
- translation max error: `2.8217` m
- yaw RMSE: `22.357` deg
- yaw mean error: `21.205` deg
- yaw max error: `24.959` deg
- RPE translation RMSE: `0.9348` m
- RPE yaw RMSE: `7.888` deg
- end-pose translation error: `2.8217` m
- end-pose yaw error: `24.940` deg
- timestamp match mean: `20.00` ms
- timestamp match max: `33.33` ms

## Evidence

- metrics JSON: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/metrics.json`
- matched samples JSON: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/matched_samples.json`
- planned path JSON: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/planned_path.json`
- occupancy ROS map dir: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/planned_occupancy_map`
- path planner log: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/path_planner.log`
- path follower runtime: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/path_follower_runtime.json`
- path follower log: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/path_follower.log`
- localization runtime: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/localization_runtime.json`
- VSLAM launch log: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/vslam_launch.log`
- localization adapter log: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/localization_adapter.log`
- evaluation log: `/home/peng/AgentSlam/artifacts/phase1/vslam_accuracy/20260317-202138/evaluation.log`

## Caveat

The route is derived from Isaac Sim occupancy data, but the final SLAM error is still compared against the executed simulator reference odometry rather than the nominal plan itself. This prevents controller tracking error from being miscounted as SLAM error.
