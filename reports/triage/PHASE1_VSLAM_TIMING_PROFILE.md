# Phase 1 VSLAM Timing Profile

## Scope

Capture topic cadence for the native Isaac Sim producer, IMU streams, chassis reference odometry, raw VSLAM odometry, and normalized localization odometry while the robot moves under a conservative `/cmd_vel` input.

## Capture Settings

- capture duration: `45.0` s
- localization active source: `primary`
- localization primary messages: `1`
- localization published messages: `9`

## Topic Summary

- `/front_stereo_camera/left/image_raw`: count `34`, mean hz `0.76`, max receive gap `5309.19` ms, tail silence `1.11` s, messages in last 10s `7`, max pose jump `0.000` m
- `/front_stereo_camera/right/image_raw`: count `38`, mean hz `0.84`, max receive gap `4322.00` ms, tail silence `0.45` s, messages in last 10s `10`, max pose jump `0.000` m
- `/front_stereo_imu/imu`: count `2442`, mean hz `54.27`, max receive gap `74.82` ms, tail silence `0.00` s, messages in last 10s `512`, max pose jump `0.000` m
- `/chassis/imu`: count `2442`, mean hz `54.27`, max receive gap `75.52` ms, tail silence `0.00` s, messages in last 10s `512`, max pose jump `0.000` m
- `/chassis/odom`: count `2441`, mean hz `54.24`, max receive gap `60.46` ms, tail silence `0.00` s, messages in last 10s `512`, max pose jump `0.001` m
- `/visual_slam/tracking/odometry`: count `0`, mean hz `0.00`, max receive gap `0.00` ms, tail silence `45.00` s, messages in last 10s `0`, max pose jump `0.000` m
- `/agentslam/localization/odom`: count `0`, mean hz `0.00`, max receive gap `0.00` ms, tail silence `45.00` s, messages in last 10s `0`, max pose jump `0.000` m
- `/cmd_vel`: count `450`, mean hz `10.00`, max receive gap `143.76` ms, tail silence `0.00` s, messages in last 10s `102`, max pose jump `0.000` m

## Motion Summary

- chassis odom path length: `1.524` m
- raw VSLAM odom path length: `0.000` m
- normalized localization odom path length: `0.000` m
- chassis odom displacement: `0.5949139325334108`
- raw VSLAM odom displacement: `None`
- normalized localization odom displacement: `None`
- raw VSLAM odom max pose jump: `0.000` m
- raw VSLAM odom jumps > 1 m: `0`
- normalized localization odom max pose jump: `0.000` m

## Evidence

- timing summary JSON: `/home/peng/AgentSlam/artifacts/phase1/timing_profile/20260317-211229/timing_summary.json`
- timing sample rows JSON: `/home/peng/AgentSlam/artifacts/phase1/timing_profile/20260317-211229/timing_samples.json`
- localization runtime JSON: `/home/peng/AgentSlam/artifacts/phase1/timing_profile/20260317-211229/localization_runtime.json`
- VSLAM launch log: `/home/peng/AgentSlam/artifacts/phase1/timing_profile/20260317-211229/vslam_launch.log`
- localization adapter log: `/home/peng/AgentSlam/artifacts/phase1/timing_profile/20260317-211229/localization_adapter.log`
- timing capture log: `/home/peng/AgentSlam/artifacts/phase1/timing_profile/20260317-211229/timing_capture.log`
