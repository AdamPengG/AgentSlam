#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: refresh_plan.sh [--report PATH]

Ask Codex to refresh the current plan and blocker summary from the latest docs and reports.
EOF
}

ROOT_DIR="$(agentslam_root)"
STAMP="$(ops_timestamp)"
REPORT_PATH="${ROOT_DIR}/reports/plan_refresh/plan_refresh_${STAMP}.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report)
      REPORT_PATH="$2"
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

mkdir -p "$(dirname "${REPORT_PATH}")"
CONTEXT_DIR="${ROOT_DIR}/artifacts/ops/codex/plan_refresh_${STAMP}"
mkdir -p "${CONTEXT_DIR}"
LATEST_NIGHTLY="$(latest_matching_file "${ROOT_DIR}/reports/nightly/nightly_phase1_eval_*.md" || true)"
CONTEXT_FILE="${CONTEXT_DIR}/plan_refresh_context.md"

cat >"${CONTEXT_FILE}" <<EOF
Read these files before responding:

- \`${ROOT_DIR}/reports/PROMPT5_STARTING_STATE.md\`
- \`${ROOT_DIR}/reports/SETUP_BLOCKERS.md\`
- \`${ROOT_DIR}/reports/PHASE1_VALIDATION.md\`
- \`${ROOT_DIR}/reports/PHASE1_REVIEW.md\`
- \`${ROOT_DIR}/docs/PLANS.md\`
- \`${ROOT_DIR}/docs/EVAL.md\`
- \`${ROOT_DIR}/docs/INTERFACES.md\`
- \`${ROOT_DIR}/docs/DATAFLOW.md\`
- latest nightly summary: \`${LATEST_NIGHTLY:-none}\`

Write the refreshed plan to:

- \`${REPORT_PATH}\`
EOF

bash "${ROOT_DIR}/scripts/ops/run_codex_exec.sh" \
  --prompt "${ROOT_DIR}/prompts/exec/plan_refresh.md" \
  --report "${REPORT_PATH}" \
  --context-file "${CONTEXT_FILE}" \
  --log-dir "${CONTEXT_DIR}" \
  --label plan_refresh

cp -f "${REPORT_PATH}" "${ROOT_DIR}/reports/plan_refresh/latest.md"
