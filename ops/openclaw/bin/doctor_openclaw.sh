#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: doctor_openclaw.sh [--deep]

Aggregate the most important OpenClaw health checks:
- status
- config validate
- plugins list
- channels status
- security audit
EOF
}

DEEP=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deep)
      DEEP=1
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

source_openclaw_env

bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/openclaw_status.sh" || true
echo
openclaw config validate || true
echo
openclaw plugins list || true
echo
openclaw channels status || true
echo
if [[ ${DEEP} -eq 1 ]]; then
  openclaw security audit --deep || true
else
  openclaw security audit || true
fi
