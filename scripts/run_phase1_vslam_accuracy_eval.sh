#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VSLAM_OVERLAY="${VSLAM_OVERLAY:-/home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash}"
ISAAC_SIM_ROOT="${ISAAC_SIM_ROOT:-/home/peng/IsaacSim}"
ISAAC_PY="${ISAAC_SIM_ROOT}/_build/linux-x86_64/release/python.sh"
ARTIFACT_ROOT="${ROOT_DIR}/artifacts/phase1/vslam_accuracy"
TIMESTAMP="${TIMESTAMP:-$(date +%Y%m%d-%H%M%S)}"
ARTIFACT_DIR="${ARTIFACT_ROOT}/${TIMESTAMP}"
REPORT_PATH="${ROOT_DIR}/reports/PHASE1_VSLAM_ACCURACY_EVAL.md"
JSON_PATH="${ARTIFACT_DIR}/metrics.json"
MATCHES_PATH="${ARTIFACT_DIR}/matched_samples.json"
PLAN_JSON="${ARTIFACT_DIR}/planned_path.json"
PLAN_MAP_DIR="${ARTIFACT_DIR}/planned_occupancy_map"
VSLAM_LOG="${ARTIFACT_DIR}/vslam_launch.log"
LOCALIZATION_LOG="${ARTIFACT_DIR}/localization_adapter.log"
EVAL_LOG="${ARTIFACT_DIR}/evaluation.log"
PLANNER_LOG="${ARTIFACT_DIR}/path_planner.log"
FOLLOWER_LOG="${ARTIFACT_DIR}/path_follower.log"
FOLLOWER_RUNTIME_JSON="${ARTIFACT_DIR}/path_follower_runtime.json"
EVAL_DURATION_SECONDS="${EVAL_DURATION_SECONDS:-180}"
CAPTURE_TIMEOUT_SECONDS="${CAPTURE_TIMEOUT_SECONDS:-150}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-150}"
REFERENCE_TOPIC="${REFERENCE_TOPIC:-/chassis/odom}"
ESTIMATE_TOPIC="${ESTIMATE_TOPIC:-/agentslam/localization/odom}"
TARGET_PATH_LENGTH_M="${TARGET_PATH_LENGTH_M:-20.0}"
SEGMENT_TARGET_LENGTH_M="${SEGMENT_TARGET_LENGTH_M:-5.5}"
START_HEADING_RAD="${START_HEADING_RAD:-0.0}"
MAX_START_HEADING_DEG="${MAX_START_HEADING_DEG:-45.0}"
MAX_TURN_DEG="${MAX_TURN_DEG:-100.0}"
FOLLOWER_TIMEOUT_SECONDS="${FOLLOWER_TIMEOUT_SECONDS:-240}"
FOLLOWER_LINEAR_SPEED_MPS="${FOLLOWER_LINEAR_SPEED_MPS:-0.35}"

mkdir -p "${ARTIFACT_DIR}"

if [[ ! -f "${VSLAM_OVERLAY}" ]]; then
  echo "missing isaac_ros_visual_slam overlay setup: ${VSLAM_OVERLAY}" >&2
  exit 1
fi
if [[ ! -x "${ISAAC_PY}" ]]; then
  echo "missing Isaac Sim python launcher: ${ISAAC_PY}" >&2
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
FOLLOWER_PID=""

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
  terminate_pid "${FOLLOWER_PID}"
  terminate_pid "${VSLAM_PID}"
  terminate_pid "${LOCALIZATION_PID}"
  bash "${ROOT_DIR}/scripts/stop_phase1_front_stereo_producer.sh" >/dev/null 2>&1 || true
}
trap cleanup EXIT

bash "${ROOT_DIR}/scripts/stop_phase1_front_stereo_producer.sh" >/dev/null 2>&1 || true

(
  unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH
  ISAAC_SIM_ROOT="${ISAAC_SIM_ROOT}" "${ISAAC_PY}" "${ROOT_DIR}/scripts/plan_office_nova_vslam_eval_path.py" \
    --output-json "${PLAN_JSON}" \
    --output-map-dir "${PLAN_MAP_DIR}" \
    --target-length-m "${TARGET_PATH_LENGTH_M}" \
    --segment-target-length-m "${SEGMENT_TARGET_LENGTH_M}" \
    --start-heading-rad "${START_HEADING_RAD}" \
    --max-start-heading-deg "${MAX_START_HEADING_DEG}" \
    --max-turn-deg "${MAX_TURN_DEG}" \
    >"${PLANNER_LOG}" 2>&1
)

ENABLE_CMD_VEL_PUBLISHER=0 WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS}" \
  bash "${ROOT_DIR}/scripts/run_phase1_front_stereo_native_producer.sh" >/dev/null

/usr/bin/python3 -m localization_adapter_pkg.ros_node \
  --runtime-output "${ARTIFACT_DIR}/localization_runtime.json" \
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
  --expect /visual_slam/tracking/odometry nav_msgs/msg/Odometry \
  --expect "${ESTIMATE_TOPIC}" nav_msgs/msg/Odometry \
  --expect "${REFERENCE_TOPIC}" nav_msgs/msg/Odometry \
  >/dev/null

/usr/bin/python3 "${ROOT_DIR}/scripts/follow_waypoint_path.py" \
  --path-json "${PLAN_JSON}" \
  --odom-topic "${REFERENCE_TOPIC}" \
  --cmd-topic /cmd_vel \
  --runtime-output "${FOLLOWER_RUNTIME_JSON}" \
  --linear-speed-mps "${FOLLOWER_LINEAR_SPEED_MPS}" \
  --timeout-seconds "${FOLLOWER_TIMEOUT_SECONDS}" \
  >"${FOLLOWER_LOG}" 2>&1 &
FOLLOWER_PID=$!

/usr/bin/python3 "${ROOT_DIR}/scripts/evaluate_odom_against_reference.py" \
  --reference-topic "${REFERENCE_TOPIC}" \
  --estimate-topic "${ESTIMATE_TOPIC}" \
  --duration-seconds "${EVAL_DURATION_SECONDS}" \
  --warmup-seconds 3.0 \
  --max-match-dt-seconds 0.05 \
  --rpe-interval-seconds 1.0 \
  --output-json "${JSON_PATH}" \
  --output-matches-json "${MATCHES_PATH}" \
  >"${EVAL_LOG}" 2>&1

terminate_pid "${FOLLOWER_PID}"
FOLLOWER_PID=""

/usr/bin/python3 - "${JSON_PATH}" "${PLAN_JSON}" "${FOLLOWER_RUNTIME_JSON}" "${REPORT_PATH}" "${ARTIFACT_DIR}" <<'PY'
import json
import sys
from pathlib import Path

metrics_path = Path(sys.argv[1])
plan_path = Path(sys.argv[2])
follower_runtime_path = Path(sys.argv[3])
report_path = Path(sys.argv[4])
artifact_dir = Path(sys.argv[5])
metrics = json.loads(metrics_path.read_text())
plan = json.loads(plan_path.read_text())
follower_runtime = json.loads(follower_runtime_path.read_text()) if follower_runtime_path.exists() else {}

report = f"""# Phase 1 VSLAM Accuracy Eval

## Scope

Evaluate AgentSlam's normalized localization output against the native Isaac Sim ROS2 reference odometry on a long Office + Nova Carter route planned from Isaac Sim occupancy data.

## Route Plan

- occupancy-based planned length: `{plan['planned_length_m']:.3f}` m
- planned turn count: `{plan['planned_turn_count']}`
- target length: `{plan['target_length_m']:.1f}` m
- path follower completed: `{follower_runtime.get('completed', False)}`
- path follower duration: `{follower_runtime.get('duration_seconds', 0.0):.2f}` s

## Reference And Estimate

- reference topic: `{metrics['reference_topic']}`
- estimate topic: `{metrics['estimate_topic']}`
- duration: `{metrics['duration_seconds']}` seconds
- warmup excluded: `{metrics['warmup_seconds']}` seconds
- matching tolerance: `{metrics['max_match_dt_seconds'] * 1000.0:.1f}` ms
- RPE interval: `{metrics['rpe_interval_seconds']}` seconds
- comparison frame: `{metrics['comparison_frame']}`

## Result

- matched samples: `{metrics['matched_sample_count']}`
- reference path length: `{metrics['reference_path_length_m']:.3f}` m
- estimate path length: `{metrics['estimate_path_length_m']:.3f}` m
- translation RMSE: `{metrics['translation_rmse_m']:.4f}` m
- translation mean error: `{metrics['translation_mean_m']:.4f}` m
- translation max error: `{metrics['translation_max_m']:.4f}` m
- yaw RMSE: `{metrics['yaw_rmse_deg']:.3f}` deg
- yaw mean error: `{metrics['yaw_mean_deg']:.3f}` deg
- yaw max error: `{metrics['yaw_max_deg']:.3f}` deg
- RPE translation RMSE: `{metrics['rpe_translation_rmse_m']:.4f}` m
- RPE yaw RMSE: `{metrics['rpe_yaw_rmse_deg']:.3f}` deg
- end-pose translation error: `{metrics['end_pose_translation_error_m']:.4f}` m
- end-pose yaw error: `{metrics['end_pose_yaw_error_deg']:.3f}` deg
- timestamp match mean: `{metrics['match_dt_mean_ms']:.2f}` ms
- timestamp match max: `{metrics['match_dt_max_ms']:.2f}` ms

## Evidence

- metrics JSON: `{artifact_dir / 'metrics.json'}`
- matched samples JSON: `{artifact_dir / 'matched_samples.json'}`
- planned path JSON: `{artifact_dir / 'planned_path.json'}`
- occupancy ROS map dir: `{artifact_dir / 'planned_occupancy_map'}`
- path planner log: `{artifact_dir / 'path_planner.log'}`
- path follower runtime: `{artifact_dir / 'path_follower_runtime.json'}`
- path follower log: `{artifact_dir / 'path_follower.log'}`
- localization runtime: `{artifact_dir / 'localization_runtime.json'}`
- VSLAM launch log: `{artifact_dir / 'vslam_launch.log'}`
- localization adapter log: `{artifact_dir / 'localization_adapter.log'}`
- evaluation log: `{artifact_dir / 'evaluation.log'}`

## Caveat

The route is derived from Isaac Sim occupancy data, but the final SLAM error is still compared against the executed simulator reference odometry rather than the nominal plan itself. This prevents controller tracking error from being miscounted as SLAM error.
"""

report_path.write_text(report)
print(report)
PY

echo "phase1 vslam accuracy eval complete"
echo "- report: ${REPORT_PATH}"
echo "- metrics: ${JSON_PATH}"
