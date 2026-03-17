#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: triage_failure.sh --input PATH [--report PATH]

Run a bounded Codex triage pass against a failing log file or directory.
EOF
}

ROOT_DIR="$(agentslam_root)"
STAMP="$(ops_timestamp)"
INPUT_PATH=""
REPORT_PATH="${ROOT_DIR}/reports/triage/triage_${STAMP}.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input)
      INPUT_PATH="$2"
      shift 2
      ;;
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

if [[ -z "${INPUT_PATH}" ]]; then
  echo "--input is required." >&2
  usage >&2
  exit 2
fi

if [[ ! -e "${INPUT_PATH}" ]]; then
  echo "Input path does not exist: ${INPUT_PATH}" >&2
  exit 1
fi

mkdir -p "$(dirname "${REPORT_PATH}")"
CONTEXT_DIR="${ROOT_DIR}/artifacts/ops/codex/triage_${STAMP}"
mkdir -p "${CONTEXT_DIR}"
CONTEXT_FILE="${CONTEXT_DIR}/triage_context.md"

cat >"${CONTEXT_FILE}" <<EOF
Primary failing input:

- \`${INPUT_PATH}\`

Read these project files for context:

- \`${ROOT_DIR}/docs/EVAL.md\`
- \`${ROOT_DIR}/docs/INTERFACES.md\`
- \`${ROOT_DIR}/docs/DATAFLOW.md\`
- \`${ROOT_DIR}/reports/SETUP_BLOCKERS.md\`

Write the final triage report to:

- \`${REPORT_PATH}\`
EOF

bash "${ROOT_DIR}/scripts/ops/run_codex_exec.sh" \
  --prompt "${ROOT_DIR}/prompts/exec/ci_failure_triage.md" \
  --report "${REPORT_PATH}" \
  --context-file "${CONTEXT_FILE}" \
  --log-dir "${CONTEXT_DIR}" \
  --label ci_failure_triage

cp -f "${REPORT_PATH}" "${ROOT_DIR}/reports/triage/latest.md"
