#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: check_codex_auth.sh [--report-path PATH] [--quiet]

Check whether Codex CLI is installed and whether ChatGPT-managed login is available.
This command does not modify auth state.

Options:
  --report-path PATH  Write a markdown summary to PATH.
  --quiet             Suppress stdout and rely on exit code or report file.
  -h, --help          Show this help message.
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_PATH=""
QUIET=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report-path)
      REPORT_PATH="$2"
      shift 2
      ;;
    --quiet)
      QUIET=1
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

CODEX_BIN="$(command -v codex || true)"
CODEX_HOME_DIR="${CODEX_HOME:-${HOME}/.codex}"
AUTH_PATH="${CODEX_HOME_DIR}/auth.json"
TIMESTAMP="$(date -Is)"
STATUS="PASS"
CODEX_VERSION="unavailable"
LOGIN_STATUS="not checked"
AUTH_STATE="missing"
ADVICE="No action needed."

if [[ -z "${CODEX_BIN}" ]]; then
  STATUS="FAIL"
  ADVICE="Install Codex CLI on the trusted runner before using codex exec."
else
  CODEX_VERSION="$(codex --version 2>/dev/null || echo unavailable)"
  if LOGIN_STATUS="$(codex login status 2>&1)"; then
    :
  else
    STATUS="FAIL"
    ADVICE="Run 'codex login' or 'codex login --device-auth' on the trusted runner."
  fi
fi

if [[ -f "${AUTH_PATH}" ]]; then
  AUTH_STATE="present"
elif [[ "${STATUS}" == "PASS" ]]; then
  AUTH_STATE="not found at expected path"
  ADVICE="Codex login works, but auth.json was not found at the expected path. Confirm CODEX_HOME on the runner."
fi

SUMMARY="$(cat <<EOF
status: ${STATUS}
timestamp: ${TIMESTAMP}
repo_root: ${ROOT_DIR}
codex_bin: ${CODEX_BIN:-missing}
codex_version: ${CODEX_VERSION}
codex_home: ${CODEX_HOME_DIR}
auth_json: ${AUTH_PATH}
auth_state: ${AUTH_STATE}
login_status: ${LOGIN_STATUS}
advice: ${ADVICE}
EOF
)"

if [[ -n "${REPORT_PATH}" ]]; then
  mkdir -p "$(dirname "${REPORT_PATH}")"
  cat >"${REPORT_PATH}" <<EOF
# Codex Auth Check

- status: ${STATUS}
- timestamp: ${TIMESTAMP}
- repo_root: \`${ROOT_DIR}\`
- codex_bin: \`${CODEX_BIN:-missing}\`
- codex_version: \`${CODEX_VERSION}\`
- codex_home: \`${CODEX_HOME_DIR}\`
- auth_json: \`${AUTH_PATH}\`
- auth_state: ${AUTH_STATE}
- login_status: ${LOGIN_STATUS}
- advice: ${ADVICE}
EOF
fi

if [[ ${QUIET} -eq 0 ]]; then
  printf '%s\n' "${SUMMARY}"
fi

if [[ "${STATUS}" == "PASS" ]]; then
  exit 0
fi

exit 1
