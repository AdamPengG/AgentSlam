#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_gitnexus_status.sh

Check the local GitNexus index state through the repo wrapper.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

bash "/home/peng/AgentSlam/scripts/run_gitnexus.sh" status
