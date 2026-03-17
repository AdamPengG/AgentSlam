#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: with_codex_lock.sh [--lock-name NAME] [--timeout SECONDS] -- <command> [args...]

Serialize access to Codex auth or any other shared runner resource using flock.

Options:
  --lock-name NAME    Lock file name without path. Default: codex-chatgpt-auth
  --timeout SECONDS   Seconds to wait for the lock. Default: 1800
  -h, --help          Show this help message.
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOCK_NAME="codex-chatgpt-auth"
TIMEOUT=1800

while [[ $# -gt 0 ]]; do
  case "$1" in
    --lock-name)
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
  echo "No command provided to run under lock." >&2
  usage >&2
  exit 2
fi

if ! command -v flock >/dev/null 2>&1; then
  echo "flock is required but not installed." >&2
  exit 1
fi

LOCK_DIR="${ROOT_DIR}/artifacts/ops/locks"
LOCK_PATH="${LOCK_DIR}/${LOCK_NAME}.lock"
mkdir -p "${LOCK_DIR}"

exec {LOCK_FD}>"${LOCK_PATH}"
if ! flock -w "${TIMEOUT}" "${LOCK_FD}"; then
  echo "Timed out waiting for lock ${LOCK_PATH} after ${TIMEOUT} seconds." >&2
  exit 1
fi

"$@"
