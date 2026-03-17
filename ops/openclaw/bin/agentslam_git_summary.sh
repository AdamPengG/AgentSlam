#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_git_summary.sh [--report-path PATH]

Write a concise git status summary for the current AgentSlam workspace.
EOF
}

ROOT_DIR="/home/peng/AgentSlam"
REPORT_PATH=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report-path)
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

SUMMARY="$(cat <<EOF
branch=$(git -C "${ROOT_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)
head=$(git -C "${ROOT_DIR}" rev-parse HEAD 2>/dev/null || echo unknown)
status:
$(git -C "${ROOT_DIR}" status --short 2>/dev/null || true)
recent_commits:
$(git -C "${ROOT_DIR}" log --oneline -5 2>/dev/null || true)
EOF
)"

if [[ -n "${REPORT_PATH}" ]]; then
  mkdir -p "$(dirname "${REPORT_PATH}")"
  cat >"${REPORT_PATH}" <<EOF
# AgentSlam Git Summary

\`\`\`text
${SUMMARY}
\`\`\`
EOF
fi

printf '%s\n' "${SUMMARY}"
