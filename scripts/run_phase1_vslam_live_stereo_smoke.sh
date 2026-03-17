#!/usr/bin/env bash
# Run a live stereo isaac_ros_visual_slam backend against the GS4/Isaac front-stereo
# contract while normalizing odometry into AgentSlam's /agentslam/localization/odom topic.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VSLAM_OVERLAY="${VSLAM_OVERLAY:-/home/peng/GS4/isaac_ros_visual_slam_ws/install/setup.bash}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-120}"
CAPTURE_TIMEOUT_SECONDS="${CAPTURE_TIMEOUT_SECONDS:-120}"
AUTO_START_PRODUCER="${AUTO_START_PRODUCER:-1}"
PRODUCER_MODE="${PRODUCER_MODE:-isaac_native_ros2}"
PRODUCER_WAIT_TIMEOUT_SECONDS="${PRODUCER_WAIT_TIMEOUT_SECONDS:-120}"
PRODUCER_START_ATTEMPTS="${PRODUCER_START_ATTEMPTS:-5}"
STOP_AUTOSTARTED_PRODUCER_ON_EXIT="${STOP_AUTOSTARTED_PRODUCER_ON_EXIT:-1}"
FRONT_STEREO_RUNTIME_DIR="${FRONT_STEREO_RUNTIME_DIR:-/home/peng/GS4/outputs/sim_gs4_master/sessions/isaac_office/agentslam_phase1_front_stereo/runtime}"
RUNTIME_PROGRESS_SAMPLES="${RUNTIME_PROGRESS_SAMPLES:-0}"
RUNTIME_PROGRESS_INTERVAL_SECONDS="${RUNTIME_PROGRESS_INTERVAL_SECONDS:-0.5}"
MIN_RUNTIME_FRAME_IDX="${MIN_RUNTIME_FRAME_IDX:-0}"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/phase1"
LOG_DIR="${ARTIFACT_DIR}/logs"
LOCALIZATION_RUNTIME="${ARTIFACT_DIR}/office_nova_vslam_live_localization_runtime.json"
RAW_ODOM_SAMPLE="${ARTIFACT_DIR}/office_nova_vslam_live_raw_odom.txt"
NORMALIZED_ODOM_SAMPLE="${ARTIFACT_DIR}/office_nova_vslam_live_localization_odom.txt"
STATUS_SAMPLE="${ARTIFACT_DIR}/office_nova_vslam_live_status.txt"
VSLAM_LOG="${LOG_DIR}/phase1_vslam_live_stereo_launch.log"
LOCALIZATION_LOG="${LOG_DIR}/phase1_vslam_live_stereo_localization.log"

LEFT_CAMERA_INFO_TOPIC="${LEFT_CAMERA_INFO_TOPIC:-/front_stereo_camera/left/camera_info}"
RIGHT_CAMERA_INFO_TOPIC="${RIGHT_CAMERA_INFO_TOPIC:-/front_stereo_camera/right/camera_info}"

if [[ "${PRODUCER_MODE}" == "isaac_native_ros2" ]]; then
  : "${LEFT_IMAGE_TOPIC:=/front_stereo_camera/left/image_raw}"
  : "${RIGHT_IMAGE_TOPIC:=/front_stereo_camera/right/image_raw}"
  : "${RECTIFIED_IMAGES:=false}"
  : "${VSLAM_BASE_FRAME:=chassis_link}"
else
  : "${LEFT_IMAGE_TOPIC:=/front_stereo_camera/left/image_rect_color}"
  : "${RIGHT_IMAGE_TOPIC:=/front_stereo_camera/right/image_rect_color}"
  : "${RECTIFIED_IMAGES:=true}"
  : "${VSLAM_BASE_FRAME:=base_link}"
fi

mkdir -p "${ARTIFACT_DIR}" "${LOG_DIR}"
rm -f \
  "${LOCALIZATION_RUNTIME}" \
  "${RAW_ODOM_SAMPLE}" \
  "${NORMALIZED_ODOM_SAMPLE}" \
  "${STATUS_SAMPLE}" \
  "${VSLAM_LOG}" \
  "${LOCALIZATION_LOG}"

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

ros2 pkg prefix isaac_ros_visual_slam >/dev/null

LOCALIZATION_PID=""
VSLAM_PID=""
RAW_ECHO_PID=""
NORMALIZED_ECHO_PID=""
STATUS_ECHO_PID=""
AUTOSTARTED_PRODUCER=0

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
  for _ in 1 2 3; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      wait "${pid}" >/dev/null 2>&1 || true
      return 0
    fi
    sleep 1
  done
  kill -KILL "${pid}" >/dev/null 2>&1 || true
  wait "${pid}" >/dev/null 2>&1 || true
}

cleanup() {
  for pid_var in STATUS_ECHO_PID NORMALIZED_ECHO_PID RAW_ECHO_PID VSLAM_PID LOCALIZATION_PID; do
    pid="${!pid_var}"
    terminate_pid "${pid}"
  done
  if [[ "${AUTOSTARTED_PRODUCER}" == "1" ]] && [[ "${STOP_AUTOSTARTED_PRODUCER_ON_EXIT}" != "0" ]]; then
    bash "${ROOT_DIR}/scripts/stop_phase1_front_stereo_producer.sh" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

wait_for_stereo_messages() {
  local timeout_s="$1"
  /usr/bin/python3 "${ROOT_DIR}/scripts/wait_for_topic_messages.py" \
    --timeout-seconds "${timeout_s}" \
    --expect "${LEFT_IMAGE_TOPIC}" sensor_msgs/msg/Image \
    --expect "${LEFT_CAMERA_INFO_TOPIC}" sensor_msgs/msg/CameraInfo \
    --expect "${RIGHT_IMAGE_TOPIC}" sensor_msgs/msg/Image \
    --expect "${RIGHT_CAMERA_INFO_TOPIC}" sensor_msgs/msg/CameraInfo \
    --expect /tf_static tf2_msgs/msg/TFMessage \
    >/dev/null
}

if ! wait_for_stereo_messages 1; then
  if [[ "${AUTO_START_PRODUCER}" == "0" ]]; then
    echo "required live stereo messages not available." >&2
    echo "start the requested front-stereo producer first, then retry this smoke." >&2
    exit 1
  fi
  if [[ "${PRODUCER_MODE}" == "isaac_native_ros2" ]]; then
    echo "live stereo messages not present; starting the native Isaac Sim front-stereo producer..." >&2
    WAIT_TIMEOUT_SECONDS="${PRODUCER_WAIT_TIMEOUT_SECONDS}" \
      bash "${ROOT_DIR}/scripts/run_phase1_front_stereo_native_producer.sh" >&2
  else
    echo "live stereo messages not present; starting the GS4 front-stereo producer..." >&2
    WAIT_TIMEOUT_SECONDS="${PRODUCER_WAIT_TIMEOUT_SECONDS}" START_ATTEMPTS="${PRODUCER_START_ATTEMPTS}" \
      bash "${ROOT_DIR}/scripts/run_phase1_front_stereo_producer.sh" >&2
  fi
  AUTOSTARTED_PRODUCER=1
fi

if [[ "${PRODUCER_MODE}" != "isaac_native_ros2" ]]; then
  if ! /usr/bin/python3 "${ROOT_DIR}/scripts/wait_for_stereo_runtime.py" \
    --runtime-dir "${FRONT_STEREO_RUNTIME_DIR}" \
    --timeout-seconds "${WAIT_TIMEOUT_SECONDS}" \
    --min-frame-idx "${MIN_RUNTIME_FRAME_IDX}" \
    --require-frame-progress "${RUNTIME_PROGRESS_SAMPLES}" \
    --progress-interval-seconds "${RUNTIME_PROGRESS_INTERVAL_SECONDS}" \
    >/dev/null; then
    echo "front-stereo runtime did not become materially ready in time." >&2
    echo "inspect ${ROOT_DIR}/artifacts/phase1/logs/front_stereo_producer" >&2
    exit 1
  fi
fi

/usr/bin/python3 -m localization_adapter_pkg.ros_node \
  --runtime-output "${LOCALIZATION_RUNTIME}" \
  >"${LOCALIZATION_LOG}" 2>&1 &
LOCALIZATION_PID=$!

ros2 launch "${ROOT_DIR}/ros_ws/launch/phase1_vslam_stereo.launch.py" \
  left_image_topic:="${LEFT_IMAGE_TOPIC}" \
  left_camera_info_topic:="${LEFT_CAMERA_INFO_TOPIC}" \
  right_image_topic:="${RIGHT_IMAGE_TOPIC}" \
  right_camera_info_topic:="${RIGHT_CAMERA_INFO_TOPIC}" \
  rectified_images:="${RECTIFIED_IMAGES}" \
  base_frame:="${VSLAM_BASE_FRAME}" \
  >"${VSLAM_LOG}" 2>&1 &
VSLAM_PID=$!

if ! wait_for_stereo_messages "${WAIT_TIMEOUT_SECONDS}"; then
  echo "required live stereo messages did not become available in time." >&2
  echo "inspect ${ROOT_DIR}/artifacts/phase1/logs/front_stereo_producer and ${VSLAM_LOG}" >&2
  exit 1
fi

sleep 2

/usr/bin/python3 "${ROOT_DIR}/scripts/capture_single_topic_message.py" \
  --topic /visual_slam/tracking/odometry \
  --msg-type nav_msgs/msg/Odometry \
  --output "${RAW_ODOM_SAMPLE}" \
  --timeout-seconds "${CAPTURE_TIMEOUT_SECONDS}" \
  >/dev/null 2>&1 &
RAW_ECHO_PID=$!
/usr/bin/python3 "${ROOT_DIR}/scripts/capture_single_topic_message.py" \
  --topic /agentslam/localization/odom \
  --msg-type nav_msgs/msg/Odometry \
  --output "${NORMALIZED_ODOM_SAMPLE}" \
  --timeout-seconds "${CAPTURE_TIMEOUT_SECONDS}" \
  >/dev/null 2>&1 &
NORMALIZED_ECHO_PID=$!
/usr/bin/python3 "${ROOT_DIR}/scripts/capture_single_topic_message.py" \
  --topic /agentslam/localization/status \
  --msg-type std_msgs/msg/String \
  --output "${STATUS_SAMPLE}" \
  --timeout-seconds "${CAPTURE_TIMEOUT_SECONDS}" \
  >/dev/null 2>&1 &
STATUS_ECHO_PID=$!

wait "${RAW_ECHO_PID}"
RAW_ECHO_PID=""
wait "${NORMALIZED_ECHO_PID}"
NORMALIZED_ECHO_PID=""
wait "${STATUS_ECHO_PID}"
STATUS_ECHO_PID=""

if [[ ! -s "${RAW_ODOM_SAMPLE}" ]] || [[ ! -s "${NORMALIZED_ODOM_SAMPLE}" ]] || [[ ! -s "${STATUS_SAMPLE}" ]]; then
  echo "failed to capture live stereo VSLAM odometry or localization status; inspect ${VSLAM_LOG}" >&2
  exit 1
fi

sleep 2
terminate_pid "${LOCALIZATION_PID}"
LOCALIZATION_PID=""
terminate_pid "${VSLAM_PID}"
VSLAM_PID=""

/usr/bin/python3 - <<'PY'
import json
from pathlib import Path

runtime = json.loads(Path("/home/peng/AgentSlam/artifacts/phase1/office_nova_vslam_live_localization_runtime.json").read_text())
if runtime.get("active_source") != "primary":
    raise SystemExit(f"expected active_source=primary, got {runtime.get('active_source')!r}")
if runtime.get("primary_messages", 0) < 1:
    raise SystemExit("expected at least one primary VSLAM odometry message")
if runtime.get("published_messages", 0) < 1:
    raise SystemExit("expected normalized localization odometry to be published")
PY

echo "phase1 live stereo vslam smoke complete"
echo "- raw_vslam_odom: ${RAW_ODOM_SAMPLE}"
echo "- normalized_odom: ${NORMALIZED_ODOM_SAMPLE}"
echo "- localization_status: ${STATUS_SAMPLE}"
echo "- localization_runtime: ${LOCALIZATION_RUNTIME}"
