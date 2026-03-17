#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_notify_telegram.sh --title TEXT --summary TEXT [--report-path PATH] [--dry-run]

Send a concise Telegram DM notification through the local OpenClaw gateway.
Requires AGENTSLAM_TELEGRAM_TARGET in the environment for live sends.
EOF
}

TITLE=""
SUMMARY=""
REPORT_PATH=""
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)
      TITLE="$2"
      shift 2
      ;;
    --summary)
      SUMMARY="$2"
      shift 2
      ;;
    --report-path)
      REPORT_PATH="$2"
      shift 2
      ;;
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

if [[ -z "${TITLE}" || -z "${SUMMARY}" ]]; then
  usage >&2
  exit 2
fi

MESSAGE="${TITLE}"$'\n'"${SUMMARY}"
if [[ -n "${REPORT_PATH}" ]]; then
  MESSAGE+=$'\n'"report: ${REPORT_PATH}"
fi

if [[ ${DRY_RUN} -eq 1 ]]; then
  printf '%s\n' "${MESSAGE}"
  exit 0
fi

if [[ -z "${AGENTSLAM_TELEGRAM_TARGET:-}" ]]; then
  echo "AGENTSLAM_TELEGRAM_TARGET is required for live Telegram sends." >&2
  exit 1
fi

openclaw message send \
  --channel telegram \
  --target "${AGENTSLAM_TELEGRAM_TARGET}" \
  --message "${MESSAGE}"
