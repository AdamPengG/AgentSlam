#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_phase1_replay_eval.sh [--dry-run]

Run the replay-backed Phase 1 evaluation path through a serialized wrapper.
EOF
}

ROOT_DIR="/home/peng/AgentSlam"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_DIR="${ROOT_DIR}/artifacts/ops/openclaw/phase1_replay/${STAMP}"
LOG_PATH="${LOG_DIR}/replay_eval.log"
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
  echo "bash scripts/run_phase1_replay_demo.sh"
  exit 0
fi

bash "${ROOT_DIR}/ops/openclaw/bin/agentslam_lock.sh" --name agentslam-phase1-replay -- \
  bash "${ROOT_DIR}/scripts/run_phase1_replay_demo.sh" >"${LOG_PATH}" 2>&1

echo "phase1_replay_log=${LOG_PATH}"
