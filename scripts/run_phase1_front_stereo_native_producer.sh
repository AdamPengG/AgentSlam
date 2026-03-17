#!/usr/bin/env bash
# Start a native Isaac Sim Office + Nova front-stereo producer without the GS4 file bridge.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAAC_SIM_ROOT="${ISAAC_SIM_ROOT:-/home/peng/IsaacSim}"
ISAAC_PY="${ISAAC_SIM_ROOT}/_build/linux-x86_64/release/python.sh"
ISAAC_ROS2_BRIDGE_LIB="${ISAAC_SIM_ROOT}/_build/linux-x86_64/release/exts/isaacsim.ros2.bridge/humble/lib"
OFFICE_SCENE="${OFFICE_SCENE:-/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd}"
NOVA_ROBOT="${NOVA_ROBOT:-/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd}"
ROBOT_PRIM_PATH="${ROBOT_PRIM_PATH:-/World/NovaCarter}"
CAMERA_NAMESPACE="${CAMERA_NAMESPACE:-front_stereo_camera}"
WAIT_TIMEOUT_SECONDS="${WAIT_TIMEOUT_SECONDS:-180}"
LOG_DIR="${LOG_DIR:-${ROOT_DIR}/artifacts/phase1/logs/front_stereo_producer}"
PIDS_FILE="${LOG_DIR}/pids.env"
ISAAC_LOG="${LOG_DIR}/native_isaac_sim.log"
CMD_VEL_LOG="${LOG_DIR}/native_cmd_vel.log"
STATIC_TF_LOG="${LOG_DIR}/native_static_tf.log"
MOTION_LINEAR_X="${MOTION_LINEAR_X:-0.05}"
MOTION_ANGULAR_Z="${MOTION_ANGULAR_Z:-0.25}"
MOTION_RATE_HZ="${MOTION_RATE_HZ:-2}"
ENABLE_CMD_VEL_PUBLISHER="${ENABLE_CMD_VEL_PUBLISHER:-1}"
DISABLE_VIEWPORT_UPDATES="${DISABLE_VIEWPORT_UPDATES:-1}"
LEFT_OPTICAL_TF_XYZ="${LEFT_OPTICAL_TF_XYZ:-0.100299996844566 0.074998001555137 0.345899982084279}"
RIGHT_OPTICAL_TF_XYZ="${RIGHT_OPTICAL_TF_XYZ:-0.100299992374257 -0.075001996994339 0.345900005926137}"
OPTICAL_TF_XYZW="${OPTICAL_TF_XYZW:--0.499999999344188 0.500000009409837 -0.499999980788213 0.500000010457762}"

mkdir -p "${LOG_DIR}"

if [[ ! -x "${ISAAC_PY}" ]]; then
  echo "Isaac Sim python not found: ${ISAAC_PY}" >&2
  exit 1
fi
if [[ ! -f "${OFFICE_SCENE}" ]]; then
  echo "missing office scene USD: ${OFFICE_SCENE}" >&2
  exit 1
fi
if [[ ! -f "${NOVA_ROBOT}" ]]; then
  echo "missing ROS-enabled Nova USD: ${NOVA_ROBOT}" >&2
  exit 1
fi

export PATH="/usr/bin:/bin:/usr/sbin:/sbin:${PATH}"
unset PYTHONHOME
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER
hash -r

set +u
source /opt/ros/humble/setup.bash
set -u

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
  if [[ -n "${pgid}" ]]; then
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
PRODUCER_MODE=isaac_native_ros2
ISAAC_SIM_PID=${ISAAC_SIM_PID:-}
CMD_VEL_PUB_PID=${CMD_VEL_PUB_PID:-}
BASELINK_TF_PID=${BASELINK_TF_PID:-}
LEFT_OPTICAL_TF_PID=${LEFT_OPTICAL_TF_PID:-}
RIGHT_OPTICAL_TF_PID=${RIGHT_OPTICAL_TF_PID:-}
EOF
}

if [[ -f "${PIDS_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${PIDS_FILE}" || true
  if [[ "${PRODUCER_MODE:-}" == "isaac_native_ros2" ]] && [[ -n "${ISAAC_SIM_PID:-}" ]] && kill -0 "${ISAAC_SIM_PID}" 2>/dev/null; then
    echo "native front-stereo producer already running with pid ${ISAAC_SIM_PID}" >&2
    echo "logs: ${LOG_DIR}" >&2
    exit 0
  fi
fi

VIEWPORT_ARG=""
if [[ "${DISABLE_VIEWPORT_UPDATES}" == "1" ]]; then
  VIEWPORT_ARG="--disable-viewport-updates"
fi

nohup setsid bash -lc "unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH PYTHONHOME; export ROS_DISTRO='humble'; export RMW_IMPLEMENTATION='rmw_fastrtps_cpp'; export LD_LIBRARY_PATH=\"\${LD_LIBRARY_PATH:-}:${ISAAC_ROS2_BRIDGE_LIB}\"; exec '${ISAAC_PY}' '${ROOT_DIR}/scripts/office_nova_native_ros2_front_stereo.py' --scene '${OFFICE_SCENE}' --robot '${NOVA_ROBOT}' --robot-prim-path '${ROBOT_PRIM_PATH}' --camera-namespace '${CAMERA_NAMESPACE}' --headless ${VIEWPORT_ARG}" \
  </dev/null >"${ISAAC_LOG}" 2>&1 &
ISAAC_SIM_PID=$!

nohup setsid ros2 run tf2_ros static_transform_publisher \
  0 0 0 0 0 0 1 base_link chassis_link \
  </dev/null >>"${STATIC_TF_LOG}" 2>&1 &
BASELINK_TF_PID=$!

nohup setsid ros2 run tf2_ros static_transform_publisher \
  ${LEFT_OPTICAL_TF_XYZ} ${OPTICAL_TF_XYZW} \
  chassis_link front_stereo_camera_left_optical \
  </dev/null >>"${STATIC_TF_LOG}" 2>&1 &
LEFT_OPTICAL_TF_PID=$!

nohup setsid ros2 run tf2_ros static_transform_publisher \
  ${RIGHT_OPTICAL_TF_XYZ} ${OPTICAL_TF_XYZW} \
  chassis_link front_stereo_camera_right_optical \
  </dev/null >>"${STATIC_TF_LOG}" 2>&1 &
RIGHT_OPTICAL_TF_PID=$!

CMD_VEL_PUB_PID=""
if [[ "${ENABLE_CMD_VEL_PUBLISHER}" == "1" ]]; then
  nohup setsid ros2 topic pub -r "${MOTION_RATE_HZ}" /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: ${MOTION_LINEAR_X}, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: ${MOTION_ANGULAR_Z}}}" \
    </dev/null >"${CMD_VEL_LOG}" 2>&1 &
  CMD_VEL_PUB_PID=$!
fi

write_pid_file

if ! /usr/bin/python3 "${ROOT_DIR}/scripts/wait_for_topic_messages.py" \
  --timeout-seconds "${WAIT_TIMEOUT_SECONDS}" \
  --expect /front_stereo_camera/left/image_raw sensor_msgs/msg/Image \
  --expect /front_stereo_camera/left/camera_info sensor_msgs/msg/CameraInfo \
  --expect /front_stereo_camera/right/image_raw sensor_msgs/msg/Image \
  --expect /front_stereo_camera/right/camera_info sensor_msgs/msg/CameraInfo \
  --expect /tf_static tf2_msgs/msg/TFMessage \
  >/dev/null; then
  echo "native front-stereo producer did not become ready in time." >&2
  terminate_pid_group "${CMD_VEL_PUB_PID:-}"
  terminate_pid_group "${RIGHT_OPTICAL_TF_PID:-}"
  terminate_pid_group "${LEFT_OPTICAL_TF_PID:-}"
  terminate_pid_group "${BASELINK_TF_PID:-}"
  terminate_pid_group "${ISAAC_SIM_PID:-}"
  rm -f "${PIDS_FILE}"
  exit 1
fi

echo "native front-stereo producer is running"
echo "- isaac_log: ${ISAAC_LOG}"
if [[ "${ENABLE_CMD_VEL_PUBLISHER}" == "1" ]]; then
  echo "- cmd_vel_log: ${CMD_VEL_LOG}"
else
  echo "- cmd_vel publisher: disabled"
fi
echo "- static_tf_log: ${STATIC_TF_LOG}"
