#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

source_openclaw_env

echo "# OpenClaw Status"
echo
openclaw --version
echo
systemctl --user status openclaw-gateway.service --no-pager || true
echo
openclaw channels status || true
