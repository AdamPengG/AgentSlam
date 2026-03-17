#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_completion_gate.sh [--dry-run] [--notify]

Check whether the current semantic-map baseline is strong enough to stop and ask
for operator review. This gate is intentionally conservative.
EOF
}

ROOT_DIR="/home/peng/AgentSlam"
STATE_DIR="${ROOT_DIR}/artifacts/ops/openclaw/completion_gate"
STATE_PATH="${STATE_DIR}/latest.json"
REPORT_PATH="${ROOT_DIR}/reports/openclaw/PHASE1_COMPLETION_GATE.md"
CONTROL_PLANE_FLAG="${ROOT_DIR}/artifacts/ops/openclaw/control_plane_ready.flag"
DRY_RUN=0
NOTIFY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --notify)
      NOTIFY=1
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

mkdir -p "${STATE_DIR}"

BUILD_PASS=0
SMOKE_PASS=0
MAP_PASS=0
HANDOFF_READY=0
CONTROL_PLANE_READY=0

if [[ -f "${ROOT_DIR}/reports/PHASE1_VALIDATION.md" ]] && grep -q "build: PASS" "${ROOT_DIR}/reports/PHASE1_VALIDATION.md"; then
  BUILD_PASS=1
fi
if [[ -f "${ROOT_DIR}/reports/PHASE1_VALIDATION.md" ]] && grep -q "bridge smoke: PASS" "${ROOT_DIR}/reports/PHASE1_VALIDATION.md"; then
  SMOKE_PASS=1
fi
if [[ -f "${ROOT_DIR}/artifacts/phase1/synthetic_semantic_map.json" || -f "${ROOT_DIR}/artifacts/phase1/office_nova_replay_semantic_map.json" ]]; then
  MAP_PASS=1
fi
if [[ -f "${ROOT_DIR}/reports/PHASE1_OPERATOR_RUNBOOK.md" && -f "${ROOT_DIR}/reports/PROMPT5_FINAL_HANDOFF.md" ]]; then
  HANDOFF_READY=1
fi
if [[ -f "${CONTROL_PLANE_FLAG}" ]]; then
  CONTROL_PLANE_READY=1
fi

READY=0
if [[ ${BUILD_PASS} -eq 1 && ${SMOKE_PASS} -eq 1 && ${MAP_PASS} -eq 1 && ${HANDOFF_READY} -eq 1 && ${CONTROL_PLANE_READY} -eq 1 ]]; then
  READY=1
fi

cat >"${STATE_PATH}" <<EOF
{
  "build_pass": ${BUILD_PASS},
  "smoke_pass": ${SMOKE_PASS},
  "map_pass": ${MAP_PASS},
  "handoff_ready": ${HANDOFF_READY},
  "control_plane_ready": ${CONTROL_PLANE_READY},
  "ready_for_user_review": ${READY}
}
EOF

cat >"${REPORT_PATH}" <<EOF
# Phase 1 Completion Gate

- build_pass: ${BUILD_PASS}
- smoke_pass: ${SMOKE_PASS}
- map_pass: ${MAP_PASS}
- handoff_ready: ${HANDOFF_READY}
- control_plane_ready: ${CONTROL_PLANE_READY}
- ready_for_user_review: ${READY}
- control_plane_flag: \`${CONTROL_PLANE_FLAG}\`
- state_json: \`${STATE_PATH}\`
EOF

if [[ ${READY} -eq 1 && ${NOTIFY} -eq 1 && ${DRY_RUN} -eq 0 ]]; then
  bash "${ROOT_DIR}/ops/openclaw/bin/agentslam_notify_telegram.sh" \
    --title "AgentSlam semantic map ready" \
    --summary "Phase 1 semantic-map baseline passed the conservative completion gate." \
    --report-path "${REPORT_PATH}"
fi

cat "${REPORT_PATH}"
