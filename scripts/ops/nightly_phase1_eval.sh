#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: nightly_phase1_eval.sh [options]

Run the Phase 1 nightly regression, snapshot outputs, and optionally ask Codex to summarize results.

Options:
  --skip-smoke            Skip bridge smoke during the suite run.
  --skip-codex-summary    Skip codex exec summary generation even if auth is available.
  --require-codex-summary Fail if codex summary generation fails.
  -h, --help              Show this help message.
EOF
}

ROOT_DIR="$(agentslam_root)"
STAMP="$(ops_timestamp)"
ARTIFACT_DIR="${ROOT_DIR}/artifacts/nightly/${STAMP}"
SUITE_REPORT="${ROOT_DIR}/reports/nightly/phase1_suite_${STAMP}.md"
SUMMARY_REPORT="${ROOT_DIR}/reports/nightly/nightly_phase1_eval_${STAMP}.md"
HANDOFF_REPORT="${ROOT_DIR}/reports/nightly/nightly_handoff_${STAMP}.md"
SUMMARY_INPUT_PATH="${ARTIFACT_DIR}/nightly_summary_inputs.md"
DELTA_PATH="${ARTIFACT_DIR}/nightly_delta.md"
SKIP_SMOKE=0
SKIP_CODEX_SUMMARY=0
REQUIRE_CODEX_SUMMARY=0
SUMMARY_EXEC_TIMEOUT=240
HANDOFF_EXEC_TIMEOUT=120

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-smoke)
      SKIP_SMOKE=1
      shift
      ;;
    --skip-codex-summary)
      SKIP_CODEX_SUMMARY=1
      shift
      ;;
    --require-codex-summary)
      REQUIRE_CODEX_SUMMARY=1
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

mkdir -p "${ARTIFACT_DIR}" "${ROOT_DIR}/reports/nightly"

SUITE_ARGS=(
  --mode nightly
  --artifact-dir "${ARTIFACT_DIR}"
  --report-path "${SUITE_REPORT}"
)

if [[ ${SKIP_SMOKE} -eq 1 ]]; then
  SUITE_ARGS+=(--skip-smoke)
fi

set +e
bash "${ROOT_DIR}/scripts/ops/phase1_ci_suite.sh" "${SUITE_ARGS[@]}"
SUITE_STATUS=$?
set -e

extract_suite_status() {
  local label="$1"
  awk -F': ' -v needle="- ${label}" '$1 == needle {print $2; exit}' "${SUITE_REPORT}"
}

compare_capture_pair() {
  local label="$1"
  local current_path="$2"
  local previous_path="$3"

  if [[ ! -f "${current_path}" ]]; then
    printf -- "- %s: current artifact missing (%s)\n" "${label}" "${current_path}"
    return
  fi

  if [[ -z "${previous_path}" || ! -f "${previous_path}" ]]; then
    printf -- "- %s: no previous artifact available; current sha256=%s\n" "${label}" "$(sha256_of_file "${current_path}")"
    return
  fi

  if cmp -s "${current_path}" "${previous_path}"; then
    printf -- "- %s: unchanged (sha256=%s)\n" "${label}" "$(sha256_of_file "${current_path}")"
    return
  fi

  printf -- "- %s: changed\n" "${label}"
  printf -- "  - current_sha256: %s\n" "$(sha256_of_file "${current_path}")"
  printf -- "  - previous_sha256: %s\n" "$(sha256_of_file "${previous_path}")"
}

compare_optional_sample() {
  local label="$1"
  local current_path="$2"
  local previous_path="$3"

  if [[ ! -f "${current_path}" ]]; then
    printf -- "- %s: current sample missing (%s)\n" "${label}" "${current_path}"
    return
  fi

  if [[ -z "${previous_path}" || ! -f "${previous_path}" ]]; then
    printf -- "- %s: no previous sample available\n" "${label}"
    return
  fi

  if cmp -s "${current_path}" "${previous_path}"; then
    printf -- "- %s: unchanged\n" "${label}"
    return
  fi

  printf -- "- %s: changed; likely sample-timing variation unless a contract field is missing\n" "${label}"
}

write_fallback_summary() {
  local summary_mode="$1"
  cat >"${SUMMARY_REPORT}" <<EOF
# Nightly Phase 1 Summary

- mode: ${summary_mode}
- suite_report: \`${SUITE_REPORT}\`
- artifact_dir: \`${ARTIFACT_DIR}\`
- delta_path: \`${DELTA_PATH}\`

## Status

- build: ${BUILD_STATUS}
- unit_tests: ${UNITTEST_STATUS}
- fixture: ${FIXTURE_STATUS}
- bridge_smoke: ${SMOKE_STATUS}

## Key Facts

- nightly suite artifacts were written under \`${ARTIFACT_DIR}\`
- captured map and query artifacts were copied into \`${ARTIFACT_DIR}/captured\`
- compare details are precomputed in \`${DELTA_PATH}\`

## Recommendation

Review \`${DELTA_PATH}\` first if you need to understand what changed relative to the previous nightly.
EOF
}

write_fallback_handoff() {
  local handoff_mode="$1"
  cat >"${HANDOFF_REPORT}" <<EOF
# Nightly Handoff

- mode: ${handoff_mode}
- completed:
  - Phase 1 nightly suite
- status:
  - build=${BUILD_STATUS}
  - unit_tests=${UNITTEST_STATUS}
  - fixture=${FIXTURE_STATUS}
  - bridge_smoke=${SMOKE_STATUS}
- follow_up:
  - review \`${SUMMARY_REPORT}\` and \`${DELTA_PATH}\`
- next_action:
  - if any stage failed, run \`bash scripts/ops/triage_failure.sh --input ${ARTIFACT_DIR}\`
EOF
}

BUILD_STATUS="$(extract_suite_status build)"
UNITTEST_STATUS="$(extract_suite_status unit_tests)"
FIXTURE_STATUS="$(extract_suite_status fixture)"
SMOKE_STATUS="$(extract_suite_status bridge_smoke)"

AUTH_OK=0
if [[ ${SKIP_CODEX_SUMMARY} -eq 0 ]]; then
  if bash "${ROOT_DIR}/scripts/ops/check_codex_auth.sh" --quiet; then
    AUTH_OK=1
  fi
fi

PREVIOUS_SUMMARY="$(latest_matching_file "${ROOT_DIR}/reports/nightly/nightly_phase1_eval_*.md" || true)"
PREVIOUS_SUITE="$(latest_matching_file_excluding "${ROOT_DIR}/reports/nightly/phase1_suite_*.md" "${SUITE_REPORT}" || true)"
PREVIOUS_SUITE_STAMP=""
PREVIOUS_ARTIFACT_DIR=""
if [[ -n "${PREVIOUS_SUITE}" ]]; then
  PREVIOUS_SUITE_STAMP="$(basename "${PREVIOUS_SUITE}" .md)"
  PREVIOUS_SUITE_STAMP="${PREVIOUS_SUITE_STAMP#phase1_suite_}"
  PREVIOUS_ARTIFACT_DIR="${ROOT_DIR}/artifacts/nightly/${PREVIOUS_SUITE_STAMP}"
fi

CURRENT_CAPTURED_DIR="${ARTIFACT_DIR}/captured"
PREVIOUS_CAPTURED_DIR=""
if [[ -n "${PREVIOUS_ARTIFACT_DIR}" ]]; then
  PREVIOUS_CAPTURED_DIR="${PREVIOUS_ARTIFACT_DIR}/captured"
fi

cat >"${DELTA_PATH}" <<EOF
# Nightly Delta

- current_suite: \`${SUITE_REPORT}\`
- previous_suite: \`${PREVIOUS_SUITE:-none}\`
- current_artifact_dir: \`${ARTIFACT_DIR}\`
- previous_artifact_dir: \`${PREVIOUS_ARTIFACT_DIR:-none}\`

## Stage Status

- build: ${BUILD_STATUS}
- unit_tests: ${UNITTEST_STATUS}
- fixture: ${FIXTURE_STATUS}
- bridge_smoke: ${SMOKE_STATUS}

## Captured Artifact Comparison
EOF

compare_capture_pair "semantic_map" \
  "${CURRENT_CAPTURED_DIR}/synthetic_semantic_map.json" \
  "${PREVIOUS_CAPTURED_DIR:+${PREVIOUS_CAPTURED_DIR}/synthetic_semantic_map.json}" >>"${DELTA_PATH}"
compare_capture_pair "query_chair" \
  "${CURRENT_CAPTURED_DIR}/query_chair.json" \
  "${PREVIOUS_CAPTURED_DIR:+${PREVIOUS_CAPTURED_DIR}/query_chair.json}" >>"${DELTA_PATH}"
compare_capture_pair "query_table" \
  "${CURRENT_CAPTURED_DIR}/query_table.json" \
  "${PREVIOUS_CAPTURED_DIR:+${PREVIOUS_CAPTURED_DIR}/query_table.json}" >>"${DELTA_PATH}"
compare_capture_pair "bridge_topics" \
  "${CURRENT_CAPTURED_DIR}/phase0_bridge_topics.txt" \
  "${PREVIOUS_CAPTURED_DIR:+${PREVIOUS_CAPTURED_DIR}/phase0_bridge_topics.txt}" >>"${DELTA_PATH}"

cat >>"${DELTA_PATH}" <<EOF

## Sample Drift Notes
EOF

compare_optional_sample "bridge_detection_sample" \
  "${CURRENT_CAPTURED_DIR}/phase0_bridge_detection_sample.txt" \
  "${PREVIOUS_CAPTURED_DIR:+${PREVIOUS_CAPTURED_DIR}/phase0_bridge_detection_sample.txt}" >>"${DELTA_PATH}"
compare_optional_sample "bridge_odom_sample" \
  "${CURRENT_CAPTURED_DIR}/phase0_bridge_odom_sample.txt" \
  "${PREVIOUS_CAPTURED_DIR:+${PREVIOUS_CAPTURED_DIR}/phase0_bridge_odom_sample.txt}" >>"${DELTA_PATH}"

cat >"${SUMMARY_INPUT_PATH}" <<EOF
# Nightly Summary Inputs

- suite_report: \`${SUITE_REPORT}\`
- delta_path: \`${DELTA_PATH}\`
- current_artifact_dir: \`${ARTIFACT_DIR}\`
- previous_summary: \`${PREVIOUS_SUMMARY:-none}\`
- previous_suite: \`${PREVIOUS_SUITE:-none}\`

## Status Snapshot

- build: ${BUILD_STATUS}
- unit_tests: ${UNITTEST_STATUS}
- fixture: ${FIXTURE_STATUS}
- bridge_smoke: ${SMOKE_STATUS}

Use the delta file instead of recomputing diffs from raw artifacts unless a stage failed.
EOF

CONTEXT_FILE="${ARTIFACT_DIR}/nightly_runtime_context.md"
cat >"${CONTEXT_FILE}" <<EOF
Read these concrete inputs first:

- suite report: \`${SUITE_REPORT}\`
- summary inputs: \`${SUMMARY_INPUT_PATH}\`
- precomputed delta: \`${DELTA_PATH}\`
- nightly artifact dir: \`${ARTIFACT_DIR}\`
- previous nightly summary: \`${PREVIOUS_SUMMARY:-none}\`
- previous nightly suite: \`${PREVIOUS_SUITE:-none}\`

Required output files for this run:

- summary report: \`${SUMMARY_REPORT}\`
- handoff report: \`${HANDOFF_REPORT}\`

If the suite failed, call out the failing stage exactly and prefer bounded triage over optimistic language.
EOF

SUMMARY_STATUS=0
HANDOFF_STATUS=0

if [[ ${SKIP_CODEX_SUMMARY} -eq 1 ]]; then
  write_fallback_summary "shell-skip"
  write_fallback_handoff "shell-skip"
elif [[ ${AUTH_OK} -eq 1 ]]; then
  write_fallback_summary "shell-fallback"
  write_fallback_handoff "shell-fallback"
else
  write_fallback_summary "shell-no-auth"
  write_fallback_handoff "shell-no-auth"
fi

if [[ ${AUTH_OK} -eq 1 ]]; then
  set +e
  bash "${ROOT_DIR}/scripts/ops/run_codex_exec.sh" \
    --prompt "${ROOT_DIR}/prompts/exec/nightly_phase1_eval.md" \
    --report "${SUMMARY_REPORT}" \
    --context-file "${CONTEXT_FILE}" \
    --log-dir "${ARTIFACT_DIR}/codex/nightly_phase1_eval" \
    --label nightly_phase1_eval \
    --exec-timeout "${SUMMARY_EXEC_TIMEOUT}"
  SUMMARY_STATUS=$?
  set -e

  if [[ ${SUMMARY_STATUS} -eq 0 ]]; then
    set +e
    bash "${ROOT_DIR}/scripts/ops/run_codex_exec.sh" \
      --prompt "${ROOT_DIR}/prompts/exec/nightly_handoff.md" \
      --report "${HANDOFF_REPORT}" \
      --context-file "${CONTEXT_FILE}" \
      --log-dir "${ARTIFACT_DIR}/codex/nightly_handoff" \
      --label nightly_handoff \
      --exec-timeout "${HANDOFF_EXEC_TIMEOUT}"
    HANDOFF_STATUS=$?
    set -e
  fi
elif [[ ${SKIP_CODEX_SUMMARY} -eq 1 ]]; then
  cat >>"${SUMMARY_REPORT}" <<EOF

## Codex Status

Codex summary generation was skipped for this run because \`--skip-codex-summary\` was requested.
EOF
  cat >>"${HANDOFF_REPORT}" <<EOF

Codex handoff generation was skipped for this run because \`--skip-codex-summary\` was requested.
EOF
else
  cat >>"${SUMMARY_REPORT}" <<EOF

## Codex Status

Codex summary generation was skipped because no usable Codex auth was detected on this runner.
EOF
  cat >>"${HANDOFF_REPORT}" <<EOF

Codex handoff generation was skipped because no usable Codex auth was detected on this runner.
EOF
fi

cp -f "${SUITE_REPORT}" "${ROOT_DIR}/reports/nightly/latest_suite.md"
cp -f "${SUMMARY_REPORT}" "${ROOT_DIR}/reports/nightly/latest_summary.md"
if [[ -f "${HANDOFF_REPORT}" ]]; then
  cp -f "${HANDOFF_REPORT}" "${ROOT_DIR}/reports/nightly/latest_handoff.md"
fi

if [[ ${SUITE_STATUS} -ne 0 ]]; then
  TRIAGE_REPORT="${ROOT_DIR}/reports/triage/nightly_triage_${STAMP}.md"
  if [[ ${AUTH_OK} -eq 1 ]]; then
    bash "${ROOT_DIR}/scripts/ops/triage_failure.sh" \
      --input "${ARTIFACT_DIR}" \
      --report "${TRIAGE_REPORT}" || true
  fi
fi

if [[ ${SUITE_STATUS} -ne 0 ]]; then
  exit "${SUITE_STATUS}"
fi

if [[ ${REQUIRE_CODEX_SUMMARY} -eq 1 && ( ${SUMMARY_STATUS} -ne 0 || ${HANDOFF_STATUS} -ne 0 ) ]]; then
  exit 1
fi

exit 0
