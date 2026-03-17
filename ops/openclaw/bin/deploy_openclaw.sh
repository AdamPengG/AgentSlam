#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: deploy_openclaw.sh [--dry-run] [--target-home DIR]

Render the repo-side OpenClaw source and deploy it into a target OpenClaw home.
The live default target is ~/.openclaw. Credentials and pairings are preserved.

Options:
  --dry-run            Render into a temporary target and print the path.
  --target-home DIR    Override the target home directory.
  -h, --help           Show this help message.
EOF
}

DRY_RUN=0
TARGET_HOME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --target-home)
      TARGET_HOME="$2"
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

ROOT_DIR="$(agentslam_root)"
STAMP="$(openclaw_timestamp)"

if [[ -z "${TARGET_HOME}" ]]; then
  if [[ ${DRY_RUN} -eq 1 ]]; then
    TARGET_HOME="$(mktemp -d)"
  else
    TARGET_HOME="${HOME}"
  fi
fi

TARGET_OPENCLAW_DIR="${TARGET_HOME}/.openclaw"
TARGET_CONFIG_PATH="${TARGET_OPENCLAW_DIR}/openclaw.json"
BACKUP_DIR="${TARGET_OPENCLAW_DIR}/backups/${STAMP}"
SHARED_SKILLS_SRC="${ROOT_DIR}/ops/openclaw/src/shared-skills"
SHARED_SKILLS_DST="${TARGET_OPENCLAW_DIR}/skills"

mkdir -p \
  "${TARGET_OPENCLAW_DIR}" \
  "${TARGET_OPENCLAW_DIR}/cron" \
  "${TARGET_OPENCLAW_DIR}/agents" \
  "${TARGET_OPENCLAW_DIR}/workspaces/agentslam/planner" \
  "${TARGET_OPENCLAW_DIR}/workspaces/agentslam/coder" \
  "${TARGET_OPENCLAW_DIR}/workspaces/agentslam/evaluator" \
  "${TARGET_OPENCLAW_DIR}/workspaces/agentslam/reporter" \
  "${SHARED_SKILLS_DST}"

if [[ ${DRY_RUN} -eq 0 ]]; then
  mkdir -p "${BACKUP_DIR}"
  if [[ -f "${TARGET_CONFIG_PATH}" ]]; then
    cp -f "${TARGET_CONFIG_PATH}" "${BACKUP_DIR}/openclaw.json"
  fi
  if [[ -f "${TARGET_OPENCLAW_DIR}/cron/jobs.json" ]]; then
    cp -f "${TARGET_OPENCLAW_DIR}/cron/jobs.json" "${BACKUP_DIR}/jobs.json"
  fi
fi

bash "${ROOT_DIR}/ops/openclaw/bin/render_openclaw.sh" --output "${TARGET_CONFIG_PATH}" >/dev/null

if [[ -d "${SHARED_SKILLS_SRC}" ]]; then
  find "${SHARED_SKILLS_DST}" -mindepth 1 -maxdepth 1 -type d -name 'agentslam-*' -exec rm -rf {} + 2>/dev/null || true
  find "${SHARED_SKILLS_SRC}" -mindepth 1 -maxdepth 1 -type d -name 'agentslam-*' -exec cp -R {} "${SHARED_SKILLS_DST}/" \;
fi

if [[ ${DRY_RUN} -eq 1 ]]; then
  echo "dry-run target_home=${TARGET_HOME}"
  echo "rendered_config=${TARGET_CONFIG_PATH}"
  exit 0
fi

echo "deployed_openclaw_home=${TARGET_OPENCLAW_DIR}"
echo "backup_dir=${BACKUP_DIR}"
echo "config=${TARGET_CONFIG_PATH}"
