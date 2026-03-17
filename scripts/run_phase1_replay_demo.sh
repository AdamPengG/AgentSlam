#!/usr/bin/env bash
# Build a rosbag from the office/nova replay fixture, then replay it into the Phase 1 mapper.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_PATH="${ROOT_DIR}/fixtures/semantic_mapping/office_nova_replay_scene.json"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/phase1"
BAG_DIR="${ARTIFACT_DIR}/office_nova_replay_bag"
QUERY_DIR="${ARTIFACT_DIR}/replay_queries"
MAP_OUTPUT="${ARTIFACT_DIR}/office_nova_replay_semantic_map.json"
CHAIR_QUERY_OUTPUT="${ARTIFACT_DIR}/query_chair_replay_cli.json"
CABINET_QUERY_OUTPUT="${ARTIFACT_DIR}/query_cabinet_replay_cli.json"
LOG_DIR="${ARTIFACT_DIR}/logs"
RECORD_LOG="${LOG_DIR}/replay_bag_record.log"
PUBLISHER_LOG="${LOG_DIR}/replay_bag_seed_publisher.log"
PLAY_LOG="${LOG_DIR}/replay_bag_play.log"
MAPPER_LOG="${LOG_DIR}/replay_mapper.log"
TOPICS=(
  /agentslam/camera/rgb/camera_info
  /agentslam/camera/rgb/image_raw
  /agentslam/camera/depth/image_raw
  /agentslam/imu/data
  /agentslam/gt/odom
  /agentslam/semantic_detections
)

mkdir -p "${ARTIFACT_DIR}" "${QUERY_DIR}" "${LOG_DIR}"
rm -rf "${BAG_DIR}" "${QUERY_DIR}"
mkdir -p "${QUERY_DIR}"
rm -f "${MAP_OUTPUT}" "${ARTIFACT_DIR}/office_nova_replay_semantic_map_runtime.json" "${CHAIR_QUERY_OUTPUT}" "${CABINET_QUERY_OUTPUT}"

set +u
source /opt/ros/humble/setup.bash
set -u
export PYTHONPATH="${ROOT_DIR}/ros_ws/src/semantic_mapper_pkg:${ROOT_DIR}/ros_ws/src/sim_bridge_pkg${PYTHONPATH:+:${PYTHONPATH}}"

RECORD_PID=""
MAPPER_PID=""
cleanup() {
  if [[ -n "${MAPPER_PID}" ]] && kill -0 "${MAPPER_PID}" 2>/dev/null; then
    kill "${MAPPER_PID}" >/dev/null 2>&1 || true
    wait "${MAPPER_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${RECORD_PID}" ]] && kill -0 "${RECORD_PID}" 2>/dev/null; then
    kill -INT "${RECORD_PID}" >/dev/null 2>&1 || true
    wait "${RECORD_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

ros2 bag record -o "${BAG_DIR}" "${TOPICS[@]}" >"${RECORD_LOG}" 2>&1 &
RECORD_PID=$!
sleep 3

/usr/bin/python3 -m sim_bridge_pkg.fixture_replay_publisher \
  --fixture "${FIXTURE_PATH}" \
  --playback-rate 2.0 \
  --source-mode bag_replay \
  >"${PUBLISHER_LOG}" 2>&1

sleep 2
kill -INT "${RECORD_PID}" >/dev/null 2>&1 || true
wait "${RECORD_PID}" >/dev/null 2>&1 || true
RECORD_PID=""

/usr/bin/python3 -m semantic_mapper_pkg.ros_node \
  --mode bag_replay \
  --output "${MAP_OUTPUT}" \
  --query-output-dir "${QUERY_DIR}" \
  --query-label chair \
  --query-label desk \
  --query-label cabinet \
  --expected-frames 3 \
  --idle-timeout 4.0 \
  >"${MAPPER_LOG}" 2>&1 &
MAPPER_PID=$!

sleep 2
ros2 bag play "${BAG_DIR}" >"${PLAY_LOG}" 2>&1
wait "${MAPPER_PID}"
MAPPER_PID=""

/usr/bin/python3 -m semantic_mapper_pkg.query_cli \
  --map "${MAP_OUTPUT}" \
  --label chair \
  --output "${CHAIR_QUERY_OUTPUT}" >/dev/null
/usr/bin/python3 -m semantic_mapper_pkg.query_cli \
  --map "${MAP_OUTPUT}" \
  --label cabinet \
  --output "${CABINET_QUERY_OUTPUT}" >/dev/null

echo "phase1 replay demo complete"
echo "- bag_dir: ${BAG_DIR}"
echo "- map_output: ${MAP_OUTPUT}"
echo "- query_dir: ${QUERY_DIR}"
echo "- cli_queries: ${CHAIR_QUERY_OUTPUT}, ${CABINET_QUERY_OUTPUT}"
