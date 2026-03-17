# Smoke Checklist

## Pre-Launch

- confirm the project is trusted in Codex CLI if multi-agent work is expected
- confirm Multi-agents is enabled if the CLI is supposed to use project roles
- confirm the chosen Isaac launcher and Python path are documented
- confirm the chosen office scene and robot asset are documented

## Runtime Startup

- start Isaac Sim with the selected launcher
- confirm ROS 2 environment is sourced
- confirm the expected launch path completes without fatal errors

## Required Topic Checks

- `/clock` is present
- `/tf` is present
- `/tf_static` is present
- one image topic is present
- one matching camera info topic is present
- one IMU topic is present
- one GT pose topic is present

## Constraint Checks

- no LiDAR topic is required for baseline success
- no point cloud topic is required for baseline success
- no custom semantic message is required for baseline success

## Artifact Checks

- logs are saved to `reports/` or another documented location
- any replay or static validation inputs are recorded
- any failure mode is written down with the exact command that triggered it
