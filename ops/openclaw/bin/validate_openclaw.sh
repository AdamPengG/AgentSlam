#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: validate_openclaw.sh

Render repo-side OpenClaw config into a temporary HOME and run:
- jq validation on the rendered file
- openclaw config validate
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_tool jq
require_tool openclaw

TMP_HOME="$(mktemp -d)"
TMP_OPENCLAW="${TMP_HOME}/.openclaw"
mkdir -p "${TMP_OPENCLAW}"

bash "$(agentslam_root)/ops/openclaw/bin/deploy_openclaw.sh" --dry-run --target-home "${TMP_HOME}" >/dev/null
jq empty "${TMP_OPENCLAW}/openclaw.json"
HOME="${TMP_HOME}" OPENCLAW_SKIP_CANVAS_HOST=1 openclaw config validate

echo "validated_temp_home=${TMP_HOME}"
echo "validated_config=${TMP_OPENCLAW}/openclaw.json"
