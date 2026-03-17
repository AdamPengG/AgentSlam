#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: render_openclaw.sh --output PATH

Render repo-side OpenClaw config fragments into one runtime JSON file.
The source fragments use a .json5 extension but intentionally contain strict JSON
so that jq can flatten them predictably.
EOF
}

OUTPUT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)
      OUTPUT_PATH="$2"
      shift 2
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

if [[ -z "${OUTPUT_PATH}" ]]; then
  echo "--output is required." >&2
  exit 2
fi

require_tool jq

CONF_ROOT="$(openclaw_source_conf_root)"
mkdir -p "$(dirname "${OUTPUT_PATH}")"

jq -s '{
  gateway: .[0],
  session: .[1],
  channels: .[2],
  tools: .[3],
  plugins: .[4],
  agents: .[5],
  bindings: .[6],
  cron: .[7],
  skills: .[8],
  browser: .[9],
  canvasHost: .[10],
  discovery: .[11]
}' \
  "${CONF_ROOT}/gateway.json5" \
  "${CONF_ROOT}/session.json5" \
  "${CONF_ROOT}/telegram.json5" \
  "${CONF_ROOT}/tools.json5" \
  "${CONF_ROOT}/plugins.json5" \
  "${CONF_ROOT}/agents.json5" \
  "${CONF_ROOT}/bindings.json5" \
  "${CONF_ROOT}/cron.json5" \
  "${CONF_ROOT}/skills.json5" \
  "${CONF_ROOT}/browser.json5" \
  "${CONF_ROOT}/canvas.json5" \
  "${CONF_ROOT}/discovery.json5" \
  >"${OUTPUT_PATH}"

printf '%s\n' "${OUTPUT_PATH}"
