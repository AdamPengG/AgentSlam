# PHASE1_FRONT_STEREO_GEOMETRY_AUDIT

## Summary
- This is a geometry-only audit.
- We first dump the actual Nova stereo camera contract from Isaac Sim, then estimate how many pixels the same board would move if we used the current published static TF instead of the actual camera pose.

## Left Camera
- fx/fy/cx/cy: `638.541` / `638.541` / `640.000` / `360.000`
- translation error norm: `0.000000` m
- rotation error: `0.000000` deg
- expected projection visible: `True`
- reprojection gap RMSE: `1.5190037148967685e-06`
- reprojection gap max: `1.5451934876148407e-06`
- expected projection error: `None`
- overlay: `/home/peng/AgentSlam/artifacts/phase1/camera_contract/20260317-201003_static_tf_fix/left_reprojection_gap.png`

## Right Camera
- fx/fy/cx/cy: `639.551` / `639.551` / `640.000` / `360.000`
- translation error norm: `0.000000` m
- rotation error: `0.000000` deg
- expected projection visible: `True`
- reprojection gap RMSE: `1.5087288534713198e-06`
- reprojection gap max: `1.5328968475282922e-06`
- expected projection error: `None`
- overlay: `/home/peng/AgentSlam/artifacts/phase1/camera_contract/20260317-201003_static_tf_fix/right_reprojection_gap.png`

## Synthetic Board
- pose summary: `{'center_world_m': [2.0998716613406287, -5.024560245017173e-05, 0.3492196557390502], 'quaternion_xyzw': [0.49961040107977145, 0.4995989223918671, 0.5003892774369486, 0.5004007742838971], 'square_size_m': 0.035, 'inner_cols': 6, 'inner_rows': 10}`

## JSON
- metrics: `/home/peng/AgentSlam/artifacts/phase1/camera_contract/20260317-201003_static_tf_fix/reprojection_metrics.json`
