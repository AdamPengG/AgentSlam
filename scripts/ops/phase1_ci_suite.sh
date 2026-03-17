#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: phase1_ci_suite.sh [options]

Run the repeatable Phase 1 build/test/fixture/smoke suite and snapshot key outputs.

Options:
  --mode NAME          Report mode label. Default: nightly
  --artifact-dir DIR   Output artifact directory. Default: artifacts/nightly/<timestamp>
  --report-path PATH   Markdown report path. Default: reports/nightly/phase1_suite_<timestamp>.md
  --skip-build         Skip colcon build.
  --skip-smoke         Skip bridge smoke.
  -h, --help           Show this help message.
EOF
}

ROOT_DIR="$(agentslam_root)"
STAMP="$(ops_timestamp)"
MODE="nightly"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/nightly/${STAMP}"
REPORT_PATH="${ROOT_DIR}/reports/nightly/phase1_suite_${STAMP}.md"
SKIP_BUILD=0
SKIP_SMOKE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --artifact-dir)
      ARTIFACT_DIR="$2"
      shift 2
      ;;
    --report-path)
      REPORT_PATH="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=1
      shift
      ;;
    --skip-smoke)
      SKIP_SMOKE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

mkdir -p "${ARTIFACT_DIR}/logs" "${ARTIFACT_DIR}/captured" "$(dirname "${REPORT_PATH}")"

BUILD_LOG="${ARTIFACT_DIR}/logs/colcon_build.log"
UNITTEST_LOG="${ARTIFACT_DIR}/logs/unittest.log"
FIXTURE_LOG="${ARTIFACT_DIR}/logs/fixture.log"
SMOKE_LOG="${ARTIFACT_DIR}/logs/bridge_smoke.log"
CAPTURED_DIR="${ARTIFACT_DIR}/captured"

BUILD_STATUS="SKIPPED"
UNITTEST_STATUS="PENDING"
FIXTURE_STATUS="PENDING"
SMOKE_STATUS="SKIPPED"
OVERALL_STATUS=0

run_command() {
  local log_path="$1"
  shift

  set +e
  "$@" >"${log_path}" 2>&1
  local rc=$?
  set -e
  return "${rc}"
}

if [[ ${SKIP_BUILD} -eq 0 ]]; then
  if run_command "${BUILD_LOG}" bash -lc "set +u; source /opt/ros/humble/setup.bash; set -u; cd '${ROOT_DIR}/ros_ws'; colcon build --packages-select sim_bridge_pkg semantic_mapper_pkg room_graph_pkg semantic_query_pkg nav2_overlay_pkg localization_adapter_pkg eval_tools_pkg"; then
    BUILD_STATUS="PASS"
  else
    BUILD_STATUS="FAIL"
    OVERALL_STATUS=1
  fi
fi

if run_command "${UNITTEST_LOG}" bash -lc "cd '${ROOT_DIR}'; PYTHONPATH='${ROOT_DIR}/ros_ws/src/semantic_mapper_pkg:${ROOT_DIR}/ros_ws/src/sim_bridge_pkg' /usr/bin/python3 -m unittest ros_ws.src.semantic_mapper_pkg.test.test_semantic_mapper ros_ws.src.semantic_mapper_pkg.test.test_runtime_contract ros_ws.src.sim_bridge_pkg.test.test_fixture_io"; then
  UNITTEST_STATUS="PASS"
else
  UNITTEST_STATUS="FAIL"
  OVERALL_STATUS=1
fi

if run_command "${FIXTURE_LOG}" bash "${ROOT_DIR}/scripts/run_phase1_fixture.sh"; then
  FIXTURE_STATUS="PASS"
else
  FIXTURE_STATUS="FAIL"
  OVERALL_STATUS=1
fi

if [[ ${SKIP_SMOKE} -eq 0 ]]; then
  if run_command "${SMOKE_LOG}" bash "${ROOT_DIR}/scripts/run_phase0_bridge_smoke.sh"; then
    SMOKE_STATUS="PASS"
  else
    SMOKE_STATUS="FAIL"
    OVERALL_STATUS=1
  fi
fi

copy_if_exists "${ROOT_DIR}/artifacts/phase1/synthetic_semantic_map.json" "${CAPTURED_DIR}/synthetic_semantic_map.json" || true
copy_if_exists "${ROOT_DIR}/artifacts/phase1/query_chair.json" "${CAPTURED_DIR}/query_chair.json" || true
copy_if_exists "${ROOT_DIR}/artifacts/phase1/query_table.json" "${CAPTURED_DIR}/query_table.json" || true
copy_if_exists "${ROOT_DIR}/artifacts/phase1/phase0_bridge_topics.txt" "${CAPTURED_DIR}/phase0_bridge_topics.txt" || true
copy_if_exists "${ROOT_DIR}/artifacts/phase1/phase0_bridge_detection_sample.txt" "${CAPTURED_DIR}/phase0_bridge_detection_sample.txt" || true
copy_if_exists "${ROOT_DIR}/artifacts/phase1/phase0_bridge_odom_sample.txt" "${CAPTURED_DIR}/phase0_bridge_odom_sample.txt" || true

cat >"${ARTIFACT_DIR}/input_snapshot.txt" <<EOF
mode=${MODE}
fixture=${ROOT_DIR}/fixtures/semantic_mapping/synthetic_gt_pose_scene.json
expected_outputs=${ROOT_DIR}/artifacts/phase1/synthetic_semantic_map.json
expected_queries=${ROOT_DIR}/artifacts/phase1/query_chair.json,${ROOT_DIR}/artifacts/phase1/query_table.json
timestamp=${STAMP}
EOF

cat >"${REPORT_PATH}" <<EOF
# Phase 1 ${MODE^} Suite

- timestamp: ${STAMP}
- artifact_dir: \`${ARTIFACT_DIR}\`
- captured_dir: \`${CAPTURED_DIR}\`

## Status

- build: ${BUILD_STATUS}
- unit_tests: ${UNITTEST_STATUS}
- fixture: ${FIXTURE_STATUS}
- bridge_smoke: ${SMOKE_STATUS}

## Commands

- build:
  - \`set +u; source /opt/ros/humble/setup.bash; set -u; cd ros_ws; colcon build --packages-select sim_bridge_pkg semantic_mapper_pkg room_graph_pkg semantic_query_pkg nav2_overlay_pkg localization_adapter_pkg eval_tools_pkg\`
- unit tests:
  - \`PYTHONPATH=${ROOT_DIR}/ros_ws/src/semantic_mapper_pkg:${ROOT_DIR}/ros_ws/src/sim_bridge_pkg /usr/bin/python3 -m unittest ros_ws.src.semantic_mapper_pkg.test.test_semantic_mapper ros_ws.src.semantic_mapper_pkg.test.test_runtime_contract ros_ws.src.sim_bridge_pkg.test.test_fixture_io\`
- fixture:
  - \`bash scripts/run_phase1_fixture.sh\`
- bridge smoke:
  - \`bash scripts/run_phase0_bridge_smoke.sh\`

## Logs

- build_log: \`${BUILD_LOG}\`
- unittest_log: \`${UNITTEST_LOG}\`
- fixture_log: \`${FIXTURE_LOG}\`
- smoke_log: \`${SMOKE_LOG}\`

## Captured Outputs

- map: \`${CAPTURED_DIR}/synthetic_semantic_map.json\`
- query_chair: \`${CAPTURED_DIR}/query_chair.json\`
- query_table: \`${CAPTURED_DIR}/query_table.json\`
- smoke_topics: \`${CAPTURED_DIR}/phase0_bridge_topics.txt\`
- smoke_detection_sample: \`${CAPTURED_DIR}/phase0_bridge_detection_sample.txt\`
- smoke_odom_sample: \`${CAPTURED_DIR}/phase0_bridge_odom_sample.txt\`
EOF

if [[ ${OVERALL_STATUS} -eq 0 ]]; then
  exit 0
fi

exit 1
