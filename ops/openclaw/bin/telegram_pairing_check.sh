#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

source_openclaw_env

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PAIRING_FILE="${HOME}/.openclaw/credentials/telegram-pairing.json"
ALLOW_FILE="${HOME}/.openclaw/credentials/telegram-default-allowFrom.json"

echo "# Telegram Pairing Status"
echo
openclaw channels status || true
echo
echo "pairing_file=${PAIRING_FILE}"
if [[ -f "${PAIRING_FILE}" ]]; then
  cat "${PAIRING_FILE}"
else
  echo "pairing_file_missing=true"
fi
echo
echo "allow_file=${ALLOW_FILE}"
if [[ -f "${ALLOW_FILE}" ]]; then
  cat "${ALLOW_FILE}"
else
  echo "allow_file_missing=true"
fi
echo
echo "repo_root=${ROOT_DIR}"
