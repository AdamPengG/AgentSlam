#!/usr/bin/env bash
# Run a localization-adapter, geometric-mapping, and semantic-mapping chain on the office replay fixture.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_PATH="${ROOT_DIR}/fixtures/semantic_mapping/office_nova_replay_scene.json"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/phase1"
LOG_DIR="${ARTIFACT_DIR}/logs"
LOCALIZATION_LOG="${LOG_DIR}/localized_adapter.log"
GEOMETRY_LOG="${LOG_DIR}/localized_geometry_mapper.log"
SEMANTIC_LOG="${LOG_DIR}/localized_semantic_mapper.log"
PUBLISHER_LOG="${LOG_DIR}/localized_replay_publisher.log"
LOCALIZATION_RUNTIME="${ARTIFACT_DIR}/office_nova_localization_runtime.json"
GEOMETRY_OUTPUT="${ARTIFACT_DIR}/office_nova_localized_occupancy.json"
SEMANTIC_OUTPUT="${ARTIFACT_DIR}/office_nova_localized_semantic_map.json"
SEMANTIC_QUERY_DIR="${ARTIFACT_DIR}/localized_queries"

mkdir -p "${ARTIFACT_DIR}" "${LOG_DIR}" "${SEMANTIC_QUERY_DIR}"
rm -f "${LOCALIZATION_RUNTIME}" "${GEOMETRY_OUTPUT}" "${ARTIFACT_DIR}/office_nova_localized_occupancy_runtime.json"
rm -f "${SEMANTIC_OUTPUT}" "${ARTIFACT_DIR}/office_nova_localized_semantic_map_runtime.json"
rm -rf "${SEMANTIC_QUERY_DIR}"
mkdir -p "${SEMANTIC_QUERY_DIR}"

set +u
source /opt/ros/humble/setup.bash
set -u
export PYTHONPATH="${ROOT_DIR}/ros_ws/src/semantic_mapper_pkg:${ROOT_DIR}/ros_ws/src/sim_bridge_pkg:${ROOT_DIR}/ros_ws/src/localization_adapter_pkg:${ROOT_DIR}/ros_ws/src/nav2_overlay_pkg${PYTHONPATH:+:${PYTHONPATH}}"

LOC_PID=""
GEOM_PID=""
SEM_PID=""
cleanup() {
  for pid in "${SEM_PID}" "${GEOM_PID}" "${LOC_PID}"; do
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" >/dev/null 2>&1 || true
      wait "${pid}" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT

/usr/bin/python3 -m localization_adapter_pkg.ros_node \
  --primary-odom-topic /visual_slam/tracking/odometry \
  --fallback-odom-topic /agentslam/gt/odom \
  --output-odom-topic /agentslam/localization/odom \
  --status-topic /agentslam/localization/status \
  --runtime-output "${LOCALIZATION_RUNTIME}" \
  >"${LOCALIZATION_LOG}" 2>&1 &
LOC_PID=$!

/usr/bin/python3 -m nav2_overlay_pkg.localized_mapping \
  --output "${GEOMETRY_OUTPUT}" \
  --expected-frames 3 \
  --idle-timeout 4.0 \
  --pose-topic /agentslam/localization/odom \
  >"${GEOMETRY_LOG}" 2>&1 &
GEOM_PID=$!

/usr/bin/python3 -m semantic_mapper_pkg.ros_node \
  --mode bag_replay \
  --output "${SEMANTIC_OUTPUT}" \
  --query-output-dir "${SEMANTIC_QUERY_DIR}" \
  --query-label chair \
  --query-label desk \
  --query-label cabinet \
  --expected-frames 3 \
  --idle-timeout 4.0 \
  --pose-topic /agentslam/localization/odom \
  >"${SEMANTIC_LOG}" 2>&1 &
SEM_PID=$!

sleep 2
/usr/bin/python3 -m sim_bridge_pkg.fixture_replay_publisher \
  --fixture "${FIXTURE_PATH}" \
  --playback-rate 2.0 \
  --startup-delay-seconds 1.0 \
  --wait-for-subscribers \
  --source-mode localized_demo \
  >"${PUBLISHER_LOG}" 2>&1

wait "${GEOM_PID}"
GEOM_PID=""
wait "${SEM_PID}"
SEM_PID=""
kill "${LOC_PID}" >/dev/null 2>&1 || true
wait "${LOC_PID}" >/dev/null 2>&1 || true
LOC_PID=""

echo "phase1 localized mapping demo complete"
echo "- localization_runtime: ${LOCALIZATION_RUNTIME}"
echo "- geometric_map: ${GEOMETRY_OUTPUT}"
echo "- semantic_map: ${SEMANTIC_OUTPUT}"
echo "- semantic_queries: ${SEMANTIC_QUERY_DIR}"
