#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_phase0_check.sh [--dry-run] [--skip-smoke]

Validate the Isaac Office + Nova baseline and optionally run the bridge smoke
check through a serialized wrapper.
EOF
}

ROOT_DIR="/home/peng/AgentSlam"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_DIR="${ROOT_DIR}/artifacts/ops/openclaw/phase0/${STAMP}"
VALIDATE_LOG="${LOG_DIR}/isaac_validate.log"
SMOKE_LOG="${LOG_DIR}/bridge_smoke.log"
DRY_RUN=0
SKIP_SMOKE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
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

mkdir -p "${LOG_DIR}"

if [[ ${DRY_RUN} -eq 1 ]]; then
  echo "bash scripts/run_isaac_office_nova.sh --validate-only"
  if [[ ${SKIP_SMOKE} -eq 0 ]]; then
    echo "bash scripts/run_phase0_bridge_smoke.sh"
  fi
  exit 0
fi

bash "${ROOT_DIR}/ops/openclaw/bin/agentslam_lock.sh" --name agentslam-phase0 -- \
  bash "${ROOT_DIR}/scripts/run_isaac_office_nova.sh" --validate-only >"${VALIDATE_LOG}" 2>&1

if [[ ${SKIP_SMOKE} -eq 0 ]]; then
  bash "${ROOT_DIR}/ops/openclaw/bin/agentslam_lock.sh" --name agentslam-phase0 -- \
    bash "${ROOT_DIR}/scripts/run_phase0_bridge_smoke.sh" >"${SMOKE_LOG}" 2>&1
fi

echo "phase0_validate_log=${VALIDATE_LOG}"
if [[ ${SKIP_SMOKE} -eq 0 ]]; then
  echo "phase0_smoke_log=${SMOKE_LOG}"
fi
