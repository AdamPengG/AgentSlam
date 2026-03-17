#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAAC_SIM_ROOT="${ISAAC_SIM_ROOT:-/home/peng/IsaacSim}"
ISAAC_PY="${ISAAC_SIM_ROOT}/_build/linux-x86_64/release/python.sh"
ISAAC_ROS2_BRIDGE_LIB="${ISAAC_SIM_ROOT}/_build/linux-x86_64/release/exts/isaacsim.ros2.bridge/humble/lib"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ARTIFACT_DIR="${ARTIFACT_DIR:-${ROOT_DIR}/artifacts/phase1/reprojection/${TIMESTAMP}}"
LOG_DIR="${ARTIFACT_DIR}/logs"
PIDS_FILE="${ARTIFACT_DIR}/pids.env"
BOARD_META_JSON="${ARTIFACT_DIR}/checkerboard_meta.json"
METRICS_JSON="${ARTIFACT_DIR}/reprojection_metrics.json"
LEFT_OVERLAY="${ARTIFACT_DIR}/left_reprojection_overlay.png"
RIGHT_OVERLAY="${ARTIFACT_DIR}/right_reprojection_overlay.png"
ISAAC_LOG="${LOG_DIR}/checkerboard_native_isaac_sim.log"
STATIC_TF_LOG="${LOG_DIR}/checkerboard_static_tf.log"
REPORT_MD="${ROOT_DIR}/reports/PHASE1_FRONT_STEREO_REPROJECTION_AUDIT.md"
LEFT_OPTICAL_TF_XYZ="${LEFT_OPTICAL_TF_XYZ:-0.100299996844566 0.074998001555137 0.345899982084279}"
RIGHT_OPTICAL_TF_XYZ="${RIGHT_OPTICAL_TF_XYZ:-0.100299992374257 -0.075001996994339 0.345900005926137}"
OPTICAL_TF_XYZW="${OPTICAL_TF_XYZW:--0.499999999344188 0.500000009409837 -0.499999980788213 0.500000010457762}"

mkdir -p "${LOG_DIR}"

export PATH="/usr/bin:/bin:/usr/sbin:/sbin:${PATH}"
unset PYTHONHOME
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PROMPT_MODIFIER
hash -r

set +u
source /opt/ros/humble/setup.bash
set -u

terminate_pid_group() {
  local pid="${1:-}"
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
    sleep 2
    kill -KILL -- "-${pgid}" >/dev/null 2>&1 || true
    wait "${pid}" >/dev/null 2>&1 || true
  fi
}

cleanup() {
  terminate_pid_group "${RIGHT_OPTICAL_TF_PID:-}"
  terminate_pid_group "${LEFT_OPTICAL_TF_PID:-}"
  terminate_pid_group "${BASELINK_TF_PID:-}"
  terminate_pid_group "${ISAAC_SIM_PID:-}"
}
trap cleanup EXIT

nohup setsid bash -lc "unset AMENT_PREFIX_PATH COLCON_PREFIX_PATH CMAKE_PREFIX_PATH PYTHONHOME; export ROS_DISTRO='humble'; export RMW_IMPLEMENTATION='rmw_fastrtps_cpp'; export LD_LIBRARY_PATH=\"\${LD_LIBRARY_PATH:-}:${ISAAC_ROS2_BRIDGE_LIB}\"; exec '${ISAAC_PY}' '${ROOT_DIR}/scripts/office_nova_native_ros2_front_stereo.py' --checkerboard '/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Props/Camera/checkerboard_6x10.usd' --board-meta-json '${BOARD_META_JSON}' --headless" \
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

/usr/bin/python3 "${ROOT_DIR}/scripts/wait_for_topic_messages.py" \
  --timeout-seconds 180 \
  --expect /front_stereo_camera/left/image_raw sensor_msgs/msg/Image \
  --expect /front_stereo_camera/left/camera_info sensor_msgs/msg/CameraInfo \
  --expect /front_stereo_camera/right/image_raw sensor_msgs/msg/Image \
  --expect /front_stereo_camera/right/camera_info sensor_msgs/msg/CameraInfo \
  --expect /tf_static tf2_msgs/msg/TFMessage \
  >/dev/null

/usr/bin/python3 "${ROOT_DIR}/scripts/audit_front_stereo_reprojection.py" \
  --board-meta-json "${BOARD_META_JSON}" \
  --output-json "${METRICS_JSON}" \
  --left-overlay "${LEFT_OVERLAY}" \
  --right-overlay "${RIGHT_OVERLAY}"

/usr/bin/python3 - <<'PY' "${METRICS_JSON}" "${REPORT_MD}" "${ARTIFACT_DIR}" "${ISAAC_LOG}" "${STATIC_TF_LOG}"
from __future__ import annotations
import json
import sys
from pathlib import Path

metrics = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
report_path = Path(sys.argv[2])
artifact_dir = Path(sys.argv[3])
isaac_log = Path(sys.argv[4])
static_tf_log = Path(sys.argv[5])

report_path.write_text(
    "\n".join(
        [
            "# PHASE1_FRONT_STEREO_REPROJECTION_AUDIT",
            "",
            "## Summary",
            f"- artifact dir: `{artifact_dir}`",
            f"- stereo mean RMSE: `{metrics['stereo_rmse_px_mean']:.3f}` px",
            f"- stereo max error: `{metrics['stereo_max_error_px']:.3f}` px",
            "",
            "## Left Camera",
            f"- RMSE: `{metrics['left_camera']['rmse_px']:.3f}` px",
            f"- max error: `{metrics['left_camera']['max_error_px']:.3f}` px",
            f"- intrinsics: fx=`{metrics['left_camera']['fx']:.3f}` fy=`{metrics['left_camera']['fy']:.3f}` cx=`{metrics['left_camera']['cx']:.3f}` cy=`{metrics['left_camera']['cy']:.3f}`",
            f"- overlay: `{metrics['left_camera']['overlay_path']}`",
            "",
            "## Right Camera",
            f"- RMSE: `{metrics['right_camera']['rmse_px']:.3f}` px",
            f"- max error: `{metrics['right_camera']['max_error_px']:.3f}` px",
            f"- intrinsics: fx=`{metrics['right_camera']['fx']:.3f}` fy=`{metrics['right_camera']['fy']:.3f}` cx=`{metrics['right_camera']['cx']:.3f}` cy=`{metrics['right_camera']['cy']:.3f}`",
            f"- overlay: `{metrics['right_camera']['overlay_path']}`",
            "",
            "## Board Pose",
            f"- board pose in chassis: `{metrics['board_pose_chassis']}`",
            f"- board bbox size: `{metrics['board_bbox_world_size_m']}`",
            "",
            "## Logs",
            f"- Isaac log: `{isaac_log}`",
            f"- static TF log: `{static_tf_log}`",
        ]
    )
    + "\n",
    encoding="utf-8",
)
PY

echo "reprojection audit complete"
echo "- artifact_dir: ${ARTIFACT_DIR}"
echo "- metrics_json: ${METRICS_JSON}"
echo "- report: ${REPORT_MD}"
