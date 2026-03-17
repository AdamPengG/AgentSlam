#!/usr/bin/env bash
# Top-level Prompt 4 demo runner: validate Isaac Office + Nova entry, smoke the bridge, then run replay demo.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "${ROOT_DIR}/scripts/run_isaac_office_nova.sh" --validate-only
bash "${ROOT_DIR}/scripts/run_phase0_bridge_smoke.sh"
bash "${ROOT_DIR}/scripts/run_phase1_replay_demo.sh"

cat <<EOF
Phase 1 office demo completed with replay-backed validation.
If you want to attempt a manual live Isaac session, start from:
bash "${ROOT_DIR}/scripts/run_isaac_office_nova.sh" --print-live-command
EOF
