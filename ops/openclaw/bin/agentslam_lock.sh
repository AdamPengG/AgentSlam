#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_lock.sh [--name NAME] [--timeout SECONDS] -- <command> [args...]

Serialize access to AgentSlam shared resources such as build, replay, eval, or
OpenClaw deployment.
EOF
}

LOCK_NAME="agentslam-openclaw"
TIMEOUT=1800

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      LOCK_NAME="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      break
      ;;
  esac
done

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 2
fi

bash "/home/peng/AgentSlam/scripts/ops/with_codex_lock.sh" \
  --lock-name "${LOCK_NAME}" \
  --timeout "${TIMEOUT}" \
  -- "$@"
