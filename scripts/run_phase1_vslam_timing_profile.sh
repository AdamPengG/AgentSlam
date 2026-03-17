#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VSLAM_OVERLAY="${VSLAM_OVERLAY:-/home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash}"
ARTIFACT_ROOT="${ROOT_DIR}/artifacts/phase1/timing_profile"
TIMESTAMP="${TIMESTAMP:-$(date +%Y%m%d-%H%M%S)}"
ARTIFACT_DIR="${ARTIFACT_ROOT}/${TIMESTAMP}"
REPORT_PATH="${ROOT_DIR}/reports/triage/PHASE1_VSLAM_TIMING_PROFILE.md"
TIMING_JSON="${ARTIFACT_DIR}/timing_summary.json"
TIMING_SAMPLES_JSON="${ARTIFACT_DIR}/timing_samples.json"
VSLAM_LOG="${ARTIFACT_DIR}/vslam_launch.log"
LOCALIZATION_LOG="${ARTIFACT_DIR}/localization_adapter.log"
CAPTURE_LOG="${ARTIFACT_DIR}/timing_capture.log"
RUNTIME_JSON="${ARTIFACT_DIR}/localization_runtime.json"
CAPTURE_DURATION_SECONDS="${CAPTURE_DURATION_SECONDS:-45}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-120}"
MOTION_LINEAR_X="${MOTION_LINEAR_X:-0.08}"
MOTION_ANGULAR_Z="${MOTION_ANGULAR_Z:-0.18}"
MOTION_RATE_HZ="${MOTION_RATE_HZ:-10}"

mkdir -p "${ARTIFACT_DIR}"

if [[ ! -f "${VSLAM_OVERLAY}" ]]; then
  echo "missing isaac_ros_visual_slam overlay setup: ${VSLAM_OVERLAY}" >&2
  exit 1
fi

export PATH="/usr/bin:/bin:/usr/sbin:/sbin:${PATH}"
unset PYTHONHOME
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER
hash -r

set +u
source /opt/ros/humble/setup.bash
source "${VSLAM_OVERLAY}"
set -u
export PYTHONPATH="${ROOT_DIR}/ros_ws/src/localization_adapter_pkg${PYTHONPATH:+:${PYTHONPATH}}"

LOCALIZATION_PID=""
VSLAM_PID=""

terminate_pid() {
  local pid="$1"
  if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
    return 0
  fi
  kill -INT "${pid}" >/dev/null 2>&1 || true
  for _ in 1 2 3 4 5; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      wait "${pid}" >/dev/null 2>&1 || true
      return 0
    fi
    sleep 1
  done
  kill -TERM "${pid}" >/dev/null 2>&1 || true
  wait "${pid}" >/dev/null 2>&1 || true
}

cleanup() {
  terminate_pid "${VSLAM_PID}"
  terminate_pid "${LOCALIZATION_PID}"
  bash "${ROOT_DIR}/scripts/stop_phase1_front_stereo_producer.sh" >/dev/null 2>&1 || true
}
trap cleanup EXIT

bash "${ROOT_DIR}/scripts/stop_phase1_front_stereo_producer.sh" >/dev/null 2>&1 || true

ENABLE_CMD_VEL_PUBLISHER=1 \
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS}" \
MOTION_LINEAR_X="${MOTION_LINEAR_X}" \
MOTION_ANGULAR_Z="${MOTION_ANGULAR_Z}" \
MOTION_RATE_HZ="${MOTION_RATE_HZ}" \
  bash "${ROOT_DIR}/scripts/run_phase1_front_stereo_native_producer.sh" >/dev/null

/usr/bin/python3 -m localization_adapter_pkg.ros_node \
  --runtime-output "${RUNTIME_JSON}" \
  >"${LOCALIZATION_LOG}" 2>&1 &
LOCALIZATION_PID=$!

ros2 launch "${ROOT_DIR}/ros_ws/launch/phase1_vslam_stereo.launch.py" \
  left_image_topic:=/front_stereo_camera/left/image_raw \
  left_camera_info_topic:=/front_stereo_camera/left/camera_info \
  right_image_topic:=/front_stereo_camera/right/image_raw \
  right_camera_info_topic:=/front_stereo_camera/right/camera_info \
  rectified_images:=false \
  base_frame:=chassis_link \
  >"${VSLAM_LOG}" 2>&1 &
VSLAM_PID=$!

/usr/bin/python3 "${ROOT_DIR}/scripts/wait_for_topic_messages.py" \
  --timeout-seconds "${WAIT_TIMEOUT_SECONDS}" \
  --expect /front_stereo_camera/left/image_raw sensor_msgs/msg/Image \
  --expect /front_stereo_camera/right/image_raw sensor_msgs/msg/Image \
  --expect /front_stereo_imu/imu sensor_msgs/msg/Imu \
  --expect /chassis/odom nav_msgs/msg/Odometry \
  --expect /visual_slam/tracking/odometry nav_msgs/msg/Odometry \
  --expect /agentslam/localization/odom nav_msgs/msg/Odometry \
  >/dev/null

/usr/bin/python3 "${ROOT_DIR}/scripts/profile_ros_topic_timing.py" \
  --duration-seconds "${CAPTURE_DURATION_SECONDS}" \
  --output-json "${TIMING_JSON}" \
  --output-samples-json "${TIMING_SAMPLES_JSON}" \
  --topic /front_stereo_camera/left/image_raw:sensor_msgs/msg/Image:left_image_raw \
  --topic /front_stereo_camera/right/image_raw:sensor_msgs/msg/Image:right_image_raw \
  --topic /front_stereo_camera/left/camera_info:sensor_msgs/msg/CameraInfo:left_camera_info \
  --topic /front_stereo_camera/right/camera_info:sensor_msgs/msg/CameraInfo:right_camera_info \
  --topic /front_stereo_imu/imu:sensor_msgs/msg/Imu:front_stereo_imu \
  --topic /chassis/imu:sensor_msgs/msg/Imu:chassis_imu \
  --topic /chassis/odom:nav_msgs/msg/Odometry:chassis_odom \
  --topic /visual_slam/tracking/odometry:nav_msgs/msg/Odometry:raw_vslam_odom \
  --topic /agentslam/localization/odom:nav_msgs/msg/Odometry:normalized_localization_odom \
  --topic /cmd_vel:geometry_msgs/msg/Twist:cmd_vel \
  >"${CAPTURE_LOG}" 2>&1

terminate_pid "${VSLAM_PID}"
VSLAM_PID=""
terminate_pid "${LOCALIZATION_PID}"
LOCALIZATION_PID=""

/usr/bin/python3 - "${TIMING_JSON}" "${RUNTIME_JSON}" "${REPORT_PATH}" "${ARTIFACT_DIR}" <<'PY'
import json
import sys
from pathlib import Path

timing_path = Path(sys.argv[1])
runtime_path = Path(sys.argv[2])
report_path = Path(sys.argv[3])
artifact_dir = Path(sys.argv[4])
timing = json.loads(timing_path.read_text())
runtime = json.loads(runtime_path.read_text()) if runtime_path.exists() else {}

topics = timing["topics"]

def line(topic_name: str) -> str:
    topic = topics[topic_name]
    return (
        f"- `{topic_name}`: count `{topic['count']}`, mean hz `{topic['mean_receive_hz']:.2f}`, "
        f"max receive gap `{topic['receive_gap_max_ms']:.2f}` ms, tail silence `{topic['tail_silence_s']:.2f}` s, "
        f"messages in last 10s `{topic['messages_last_10s']}`, "
        f"max pose jump `{topic['pose_step_jump_max_m']:.3f}` m"
    )

report = f"""# Phase 1 VSLAM Timing Profile

## Scope

Capture topic cadence for the native Isaac Sim producer, IMU streams, chassis reference odometry, raw VSLAM odometry, and normalized localization odometry while the robot moves under a conservative `/cmd_vel` input.

## Capture Settings

- capture duration: `{timing['capture_duration_seconds']}` s
- localization active source: `{runtime.get('active_source', 'unknown')}`
- localization primary messages: `{runtime.get('primary_messages', 0)}`
- localization published messages: `{runtime.get('published_messages', 0)}`

## Topic Summary

{line('/front_stereo_camera/left/image_raw')}
{line('/front_stereo_camera/right/image_raw')}
{line('/front_stereo_imu/imu')}
{line('/chassis/imu')}
{line('/chassis/odom')}
{line('/visual_slam/tracking/odometry')}
{line('/agentslam/localization/odom')}
{line('/cmd_vel')}

## Motion Summary

- chassis odom path length: `{topics['/chassis/odom']['pose_path_length_m']:.3f}` m
- raw VSLAM odom path length: `{topics['/visual_slam/tracking/odometry']['pose_path_length_m']:.3f}` m
- normalized localization odom path length: `{topics['/agentslam/localization/odom']['pose_path_length_m']:.3f}` m
- chassis odom displacement: `{topics['/chassis/odom']['pose_displacement_m']}`
- raw VSLAM odom displacement: `{topics['/visual_slam/tracking/odometry']['pose_displacement_m']}`
- normalized localization odom displacement: `{topics['/agentslam/localization/odom']['pose_displacement_m']}`
- raw VSLAM odom max pose jump: `{topics['/visual_slam/tracking/odometry']['pose_step_jump_max_m']:.3f}` m
- raw VSLAM odom jumps > 1 m: `{topics['/visual_slam/tracking/odometry']['pose_step_jump_count_gt_1m']}`
- normalized localization odom max pose jump: `{topics['/agentslam/localization/odom']['pose_step_jump_max_m']:.3f}` m

## Evidence

- timing summary JSON: `{artifact_dir / 'timing_summary.json'}`
- timing sample rows JSON: `{artifact_dir / 'timing_samples.json'}`
- localization runtime JSON: `{artifact_dir / 'localization_runtime.json'}`
- VSLAM launch log: `{artifact_dir / 'vslam_launch.log'}`
- localization adapter log: `{artifact_dir / 'localization_adapter.log'}`
- timing capture log: `{artifact_dir / 'timing_capture.log'}`
"""

report_path.write_text(report)
print(report)
PY

echo "phase1 vslam timing profile complete"
echo "- report: ${REPORT_PATH}"
echo "- timing summary: ${TIMING_JSON}"
