#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_phase1_fixture.sh [--dry-run]

Run the validated Phase 1 fixture path through a serialized wrapper.
EOF
}

ROOT_DIR="/home/peng/AgentSlam"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_DIR="${ROOT_DIR}/artifacts/ops/openclaw/phase1_fixture/${STAMP}"
LOG_PATH="${LOG_DIR}/fixture.log"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
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
  echo "bash scripts/run_phase1_fixture.sh"
  exit 0
fi

bash "${ROOT_DIR}/ops/openclaw/bin/agentslam_lock.sh" --name agentslam-phase1-fixture -- \
  bash "${ROOT_DIR}/scripts/run_phase1_fixture.sh" >"${LOG_PATH}" 2>&1

echo "fixture_log=${LOG_PATH}"
