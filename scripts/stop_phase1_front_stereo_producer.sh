#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${LOG_DIR:-${ROOT_DIR}/artifacts/phase1/logs/front_stereo_producer}"
PIDS_FILE="${LOG_DIR}/pids.env"

if [[ ! -f "${PIDS_FILE}" ]]; then
  echo "no saved producer pid file: ${PIDS_FILE}" >&2
  exit 1
fi

terminate_pid() {
  local pid="$1"
  if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
    return 0
  fi
  kill -INT "${pid}" >/dev/null 2>&1 || true
  for _ in 1 2 3 4 5; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      wait "${pid}" >/dev/null 2>&1 || true
      return 0
    fi
    sleep 1
  done
  kill -TERM "${pid}" >/dev/null 2>&1 || true
  for _ in 1 2 3; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      wait "${pid}" >/dev/null 2>&1 || true
      return 0
    fi
    sleep 1
  done
  kill -KILL "${pid}" >/dev/null 2>&1 || true
  wait "${pid}" >/dev/null 2>&1 || true
}

terminate_pid_group() {
  local pid="$1"
  local pgid=""
  if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
    return 0
  fi
  pgid="$(ps -o pgid= -p "${pid}" 2>/dev/null | tr -d '[:space:]')"
  if [[ -n "${pgid}" ]]; then
    kill -INT -- "-${pgid}" >/dev/null 2>&1 || true
    for _ in 1 2 3 4 5; do
      if ! kill -0 "${pid}" 2>/dev/null; then
        wait "${pid}" >/dev/null 2>&1 || true
        return 0
      fi
      sleep 1
    done
    kill -TERM -- "-${pgid}" >/dev/null 2>&1 || true
    for _ in 1 2 3; do
      if ! kill -0 "${pid}" 2>/dev/null; then
        wait "${pid}" >/dev/null 2>&1 || true
        return 0
      fi
      sleep 1
    done
    kill -KILL -- "-${pgid}" >/dev/null 2>&1 || true
    wait "${pid}" >/dev/null 2>&1 || true
    return 0
  fi
  terminate_pid "${pid}"
}

# shellcheck disable=SC1090
source "${PIDS_FILE}"

terminate_pid "${FOUNDATION_PID:-}"
terminate_pid_group "${BRIDGE_PID:-}"
terminate_pid_group "${WORKER_PID:-}"

rm -f "${PIDS_FILE}"
echo "front-stereo producer stopped"
