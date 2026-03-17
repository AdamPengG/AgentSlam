#!/usr/bin/env bash
# Smoke-check the Phase 0/1 bridge contract using the fixture-based ROS publisher.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_PATH="${ROOT_DIR}/fixtures/semantic_mapping/office_nova_replay_scene.json"
TOPIC_LIST_PATH="${ROOT_DIR}/artifacts/phase1/phase0_bridge_topics.txt"
DETECTIONS_SAMPLE_PATH="${ROOT_DIR}/artifacts/phase1/phase0_bridge_detection_sample.txt"
ODOM_SAMPLE_PATH="${ROOT_DIR}/artifacts/phase1/phase0_bridge_odom_sample.txt"
PUBLISHER_LOG_PATH="${ROOT_DIR}/artifacts/phase1/phase0_bridge_publisher.log"
TOPICS=(
  /agentslam/camera/rgb/camera_info
  /agentslam/camera/rgb/image_raw
  /agentslam/camera/depth/image_raw
  /agentslam/imu/data
  /agentslam/gt/odom
  /agentslam/semantic_detections
)

mkdir -p "${ROOT_DIR}/artifacts/phase1"

bash "${ROOT_DIR}/scripts/run_isaac_office_nova.sh" --validate-only >/dev/null

set +u
source /opt/ros/humble/setup.bash
set -u
export PYTHONPATH="${ROOT_DIR}/ros_ws/src/semantic_mapper_pkg:${ROOT_DIR}/ros_ws/src/sim_bridge_pkg${PYTHONPATH:+:${PYTHONPATH}}"

PUBLISH_PID=""
cleanup() {
  if [[ -n "${PUBLISH_PID}" ]] && kill -0 "${PUBLISH_PID}" 2>/dev/null; then
    kill "${PUBLISH_PID}" >/dev/null 2>&1 || true
    wait "${PUBLISH_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

/usr/bin/python3 -m sim_bridge_pkg.fixture_replay_publisher \
  --fixture "${FIXTURE_PATH}" \
  --loop \
  --playback-rate 1.0 \
  --source-mode live_isaac \
  >"${PUBLISHER_LOG_PATH}" 2>&1 &
PUBLISH_PID=$!

sleep 3
ros2 topic list | sort >"${TOPIC_LIST_PATH}"
timeout 10s ros2 topic echo /agentslam/semantic_detections --once >"${DETECTIONS_SAMPLE_PATH}"
timeout 10s ros2 topic echo /agentslam/gt/odom --once >"${ODOM_SAMPLE_PATH}"

for topic in "${TOPICS[@]}"; do
  if ! grep -qx "${topic}" "${TOPIC_LIST_PATH}"; then
    echo "missing expected topic during bridge smoke: ${topic}" >&2
    exit 1
  fi
done

echo "phase0 bridge smoke complete"
echo "- topics: ${TOPIC_LIST_PATH}"
echo "- detection_sample: ${DETECTIONS_SAMPLE_PATH}"
echo "- odom_sample: ${ODOM_SAMPLE_PATH}"
