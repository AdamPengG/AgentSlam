#!/usr/bin/env bash
# Start the GS4 Isaac + Nova front-stereo producer so AgentSlam can consume
# /front_stereo_camera/{left,right} topics for VSLAM bring-up.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GS4_ROOT="${GS4_ROOT:-/home/peng/GS4}"
GS4_REPO="${GS4_REPO:-${GS4_ROOT}/sim_gs4_master}"
ISAAC_SIM_ROOT="${ISAAC_SIM_ROOT:-/home/peng/IsaacSim}"
ISAAC_STAGE="${ISAAC_STAGE:-/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd}"
SESSION_ID="${SESSION_ID:-agentslam_phase1_front_stereo}"
SCENE_NAME="${SCENE_NAME:-isaac_office}"
SESSION_DIR="${SESSION_DIR:-${GS4_ROOT}/outputs/sim_gs4_master/sessions/${SCENE_NAME}/${SESSION_ID}}"
RUNTIME_DIR="${RUNTIME_DIR:-${SESSION_DIR}/runtime}"
LOG_DIR="${LOG_DIR:-${ROOT_DIR}/artifacts/phase1/logs/front_stereo_producer}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-90}"
HEADLESS_FLAG="${HEADLESS_FLAG:-}"
ROBOT_MODEL="${ROBOT_MODEL:-nova_carter}"
WAIT_FOR_STEREO_TOPICS="${WAIT_FOR_STEREO_TOPICS:-1}"
START_ATTEMPTS="${START_ATTEMPTS:-5}"
RETRY_BACKOFF_SECONDS="${RETRY_BACKOFF_SECONDS:-5}"
REQUIRE_FOUNDATION_PASS="${REQUIRE_FOUNDATION_PASS:-1}"
REQUIRE_RUNTIME_PROGRESS="${REQUIRE_RUNTIME_PROGRESS:-0}"
RUNTIME_PROGRESS_INTERVAL_SECONDS="${RUNTIME_PROGRESS_INTERVAL_SECONDS:-0.5}"
MIN_RUNTIME_FRAME_IDX="${MIN_RUNTIME_FRAME_IDX:-0}"
HEALTH_STABILIZATION_SECONDS="${HEALTH_STABILIZATION_SECONDS:-8}"

ISAAC_PY="${ISAAC_SIM_ROOT}/_build/linux-x86_64/release/python.sh"
ISAAC_ROS2_BRIDGE_LIB="${ISAAC_SIM_ROOT}/_build/linux-x86_64/release/exts/isaacsim.ros2.bridge/humble/lib"
WORKER_LOG="${LOG_DIR}/live_isaac_worker.log"
BRIDGE_LOG="${LOG_DIR}/stereo_bridge.log"
FOUNDATION_LOG="${LOG_DIR}/foundation_check.txt"
PIDS_FILE="${LOG_DIR}/pids.env"

mkdir -p "${LOG_DIR}" "${SESSION_DIR}" "${RUNTIME_DIR}"
mkdir -p "${RUNTIME_DIR}/live_frames" "${RUNTIME_DIR}/orb_frames" "${RUNTIME_DIR}/fastlivo_imu_chunks" "${RUNTIME_DIR}/fastlivo_lidar_frames"

if [[ ! -x "${ISAAC_PY}" ]]; then
  echo "Isaac Sim python not found: ${ISAAC_PY}" >&2
  exit 1
fi
if [[ ! -f "${GS4_REPO}/scripts/live_isaac_worker.py" ]]; then
  echo "GS4 live_isaac_worker.py not found under ${GS4_REPO}" >&2
  exit 1
fi
if [[ ! -f "${GS4_REPO}/scripts/verify_isaac_foundation_contract.py" ]]; then
  echo "GS4 verify_isaac_foundation_contract.py not found under ${GS4_REPO}" >&2
  exit 1
fi

export PATH="/usr/bin:/bin:/usr/sbin:/sbin:${PATH}"
unset PYTHONHOME
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER
hash -r

set +u
source /opt/ros/humble/setup.bash
set -u
export PYTHONPATH="${GS4_ROOT}:${PYTHONPATH:+:${PYTHONPATH}}"

clear_runtime_artifacts() {
  rm -f \
    "${RUNTIME_DIR}/camera_info.json" \
    "${RUNTIME_DIR}/gt_pose.json" \
    "${RUNTIME_DIR}/worker_state.json" \
    "${RUNTIME_DIR}/front_stereo_contract_status.json" \
    "${RUNTIME_DIR}/isaac_timing.json" \
    "${RUNTIME_DIR}/live_frames/rgb.png" \
    "${RUNTIME_DIR}/live_frames/rgb_right.png" \
    "${RUNTIME_DIR}/live_frames/rgb_vis.png" \
    "${RUNTIME_DIR}/live_frames/depth_vis.png" \
    "${RUNTIME_DIR}/live_frames/sem_vis.png"
}

wait_for_stereo_messages() {
  local timeout_s="$1"
  /usr/bin/python3 "${ROOT_DIR}/scripts/wait_for_topic_messages.py" \
    --timeout-seconds "${timeout_s}" \
    --expect /front_stereo_camera/left/image_rect_color sensor_msgs/msg/Image \
    --expect /front_stereo_camera/left/camera_info sensor_msgs/msg/CameraInfo \
    --expect /front_stereo_camera/right/image_rect_color sensor_msgs/msg/Image \
    --expect /front_stereo_camera/right/camera_info sensor_msgs/msg/CameraInfo \
    --expect /tf_static tf2_msgs/msg/TFMessage \
    >/dev/null
}

wait_for_stereo_runtime_progress() {
  /usr/bin/python3 "${ROOT_DIR}/scripts/wait_for_stereo_runtime.py" \
    --runtime-dir "${RUNTIME_DIR}" \
    --timeout-seconds "${WAIT_TIMEOUT_SECONDS}" \
    --min-frame-idx "${MIN_RUNTIME_FRAME_IDX}" \
    --require-frame-progress "${REQUIRE_RUNTIME_PROGRESS}" \
    --progress-interval-seconds "${RUNTIME_PROGRESS_INTERVAL_SECONDS}" \
    >/dev/null
}

wait_for_worker_stability() {
  local duration_s="$1"
  local deadline=$((SECONDS + duration_s))
  while (( SECONDS <= deadline )); do
    if [[ -z "${WORKER_PID:-}" ]] || ! kill -0 "${WORKER_PID}" 2>/dev/null; then
      return 1
    fi
    if [[ -z "${BRIDGE_PID:-}" ]] || ! kill -0 "${BRIDGE_PID}" 2>/dev/null; then
      return 1
    fi
    sleep 1
  done
  return 0
}

wait_for_helper_or_runtime_health() {
  local helper_pid="$1"
  local helper_name="$2"
  while true; do
    if ! kill -0 "${helper_pid}" 2>/dev/null; then
      wait "${helper_pid}"
      return $?
    fi
    if [[ -z "${WORKER_PID:-}" ]] || ! kill -0 "${WORKER_PID}" 2>/dev/null; then
      echo "${helper_name} aborted because the Isaac worker exited before readiness completed." >&2
      terminate_pid "${helper_pid}"
      return 1
    fi
    if [[ -z "${BRIDGE_PID:-}" ]] || ! kill -0 "${BRIDGE_PID}" 2>/dev/null; then
      echo "${helper_name} aborted because the stereo bridge exited before readiness completed." >&2
      terminate_pid "${helper_pid}"
      return 1
    fi
    sleep 1
  done
}

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

terminate_pid_group() {
  local pid="$1"
  local pgid=""
  if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
    return 0
  fi
  pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d '[:space:]')"
  if [[ -n "${pgid}" ]] && [[ "${pgid}" != "$(ps -o pgid= -p $$ | tr -d '[:space:]')" ]]; then
    kill -INT -- "-${pgid}" >/dev/null 2>&1 || true
    for _ in 1 2 3 4 5; do
      if ! kill -0 "${pid}" 2>/dev/null; then
        wait "${pid}" >/dev/null 2>&1 || true
        return 0
      fi
      sleep 1
    done
    kill -TERM -- "-${pgid}" >/dev/null 2>&1 || true
    for _ in 1 2 3; do
      if ! kill -0 "${pid}" 2>/dev/null; then
        wait "${pid}" >/dev/null 2>&1 || true
        return 0
      fi
      sleep 1
    done
    kill -KILL -- "-${pgid}" >/dev/null 2>&1 || true
    wait "${pid}" >/dev/null 2>&1 || true
    return 0
  fi
  terminate_pid "${pid}"
}

write_pid_file() {
  cat >"${PIDS_FILE}" <<EOF
WORKER_PID=${WORKER_PID:-}
BRIDGE_PID=${BRIDGE_PID:-}
FOUNDATION_PID=${FOUNDATION_PID:-}
SESSION_DIR=${SESSION_DIR}
RUNTIME_DIR=${RUNTIME_DIR}
EOF
}

stop_attempt_processes() {
  terminate_pid "${FOUNDATION_PID:-}"
  terminate_pid_group "${BRIDGE_PID:-}"
  terminate_pid_group "${WORKER_PID:-}"
  WORKER_PID=""
  BRIDGE_PID=""
  FOUNDATION_PID=""
}

if [[ -f "${PIDS_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${PIDS_FILE}" || true
  if [[ -n "${WORKER_PID:-}" ]] && kill -0 "${WORKER_PID}" 2>/dev/null; then
    echo "front-stereo worker already running with pid ${WORKER_PID}" >&2
    echo "logs: ${LOG_DIR}" >&2
    exit 0
  fi
fi

attempt=1
while (( attempt <= START_ATTEMPTS )); do
  clear_runtime_artifacts

  nohup setsid bash -lc "unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH PYTHONHOME; export OLD_PYTHONPATH=\${PYTHONPATH:-}; export PYTHONPATH='${GS4_ROOT}'; export ROS_DISTRO='humble'; export RMW_IMPLEMENTATION='rmw_fastrtps_cpp'; export LD_LIBRARY_PATH=\"\${LD_LIBRARY_PATH:-}:${ISAAC_ROS2_BRIDGE_LIB}\"; exec '${ISAAC_PY}' '${GS4_REPO}/scripts/live_isaac_worker.py' ${HEADLESS_FLAG} --stage_usd '${ISAAC_STAGE}' --session_dir '${SESSION_DIR}' --runtime_dir '${RUNTIME_DIR}' --physics_hz '100' --fps '30' --max_lin_mps '0.12' --max_ang_rps '0.8' --width '640' --height '480' --render_steps_per_frame '4' --robot_model '${ROBOT_MODEL}'" \
    </dev/null >"${WORKER_LOG}" 2>&1 &
  WORKER_PID=$!

  nohup setsid /usr/bin/python3 -u -m sim_gs4_master.ros2.gs4_ros2_bridge.bridge_node \
    --ros-args -p session_dir:="${SESSION_DIR}" -p runtime_dir:="${RUNTIME_DIR}" -p stereo_only:=true \
    </dev/null >"${BRIDGE_LOG}" 2>&1 &
  BRIDGE_PID=$!
  FOUNDATION_PID=""

  attempt_ok=1
  if [[ "${REQUIRE_FOUNDATION_PASS}" != "0" ]]; then
    /usr/bin/python3 -u "${GS4_REPO}/scripts/verify_isaac_foundation_contract.py" \
      --runtime_dir "${RUNTIME_DIR}" \
      --wait_timeout_s "${WAIT_TIMEOUT_SECONDS}" \
      --require_bridge_status_images \
      >"${FOUNDATION_LOG}" 2>&1 &
    FOUNDATION_PID=$!
    if ! wait_for_helper_or_runtime_health "${FOUNDATION_PID}" "foundation contract check"; then
      attempt_ok=0
    fi
    FOUNDATION_PID=""
  fi

  if [[ "${attempt_ok}" == "1" ]] && [[ "${WAIT_FOR_STEREO_TOPICS}" != "0" ]]; then
    wait_for_stereo_messages "${WAIT_TIMEOUT_SECONDS}" >/dev/null 2>&1 &
    helper_pid=$!
    if ! wait_for_helper_or_runtime_health "${helper_pid}" "stereo topic wait"; then
      attempt_ok=0
    fi
  fi

  if [[ "${attempt_ok}" == "1" ]]; then
    wait_for_stereo_runtime_progress >/dev/null 2>&1 &
    helper_pid=$!
    if ! wait_for_helper_or_runtime_health "${helper_pid}" "runtime progress wait"; then
      attempt_ok=0
    fi
  fi

  if [[ "${attempt_ok}" == "1" ]]; then
    if ! wait_for_worker_stability "${HEALTH_STABILIZATION_SECONDS}"; then
      echo "readiness completed but the worker/bridge did not remain healthy for ${HEALTH_STABILIZATION_SECONDS}s." >&2
      attempt_ok=0
    fi
  fi

  if [[ "${attempt_ok}" == "1" ]]; then
    write_pid_file
    disown -a >/dev/null 2>&1 || true
    echo "front-stereo producer is running"
    echo "- session_dir: ${SESSION_DIR}"
    echo "- runtime_dir: ${RUNTIME_DIR}"
    echo "- worker_log: ${WORKER_LOG}"
    echo "- bridge_log: ${BRIDGE_LOG}"
    echo "- foundation_log: ${FOUNDATION_LOG}"
    echo "- pids_file: ${PIDS_FILE}"
    exit 0
  fi

  if (( attempt < START_ATTEMPTS )); then
    echo "front-stereo producer attempt ${attempt}/${START_ATTEMPTS} failed; retrying after cleanup." >&2
    echo "inspect ${WORKER_LOG}, ${BRIDGE_LOG}, and ${FOUNDATION_LOG}" >&2
  else
    echo "front-stereo producer attempt ${attempt}/${START_ATTEMPTS} failed; no attempts remain." >&2
    echo "inspect ${WORKER_LOG}, ${BRIDGE_LOG}, and ${FOUNDATION_LOG}" >&2
  fi
  stop_attempt_processes
  if (( attempt < START_ATTEMPTS )); then
    sleep "${RETRY_BACKOFF_SECONDS}"
  fi
  attempt=$((attempt + 1))
done

echo "front-stereo producer failed after ${START_ATTEMPTS} attempts." >&2
echo "inspect ${WORKER_LOG}, ${BRIDGE_LOG}, and ${FOUNDATION_LOG}" >&2
exit 1
