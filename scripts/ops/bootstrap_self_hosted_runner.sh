#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

usage() {
  cat <<'EOF'
Usage: bootstrap_self_hosted_runner.sh [options]

Create a safe, local bootstrap scaffold for an AgentSlam self-hosted runner without registering it.

Options:
  --runner-root DIR  Root directory for the generated scaffold.
                     Default: artifacts/ops/self_hosted_runner_bootstrap
  --service-user USR Suggested Unix user for the service template. Default: current user
  --labels CSV       Suggested runner labels. Default: self-hosted,linux,agentslam
  -h, --help         Show this help message.
EOF
}

ROOT_DIR="$(agentslam_root)"
RUNNER_ROOT="${ROOT_DIR}/artifacts/ops/self_hosted_runner_bootstrap"
SERVICE_USER="$(id -un)"
LABELS="self-hosted,linux,agentslam"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --runner-root)
      RUNNER_ROOT="$2"
      shift 2
      ;;
    --service-user)
      SERVICE_USER="$2"
      shift 2
      ;;
    --labels)
      LABELS="$2"
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

mkdir -p \
  "${RUNNER_ROOT}/bin" \
  "${RUNNER_ROOT}/config" \
  "${RUNNER_ROOT}/downloads" \
  "${RUNNER_ROOT}/logs" \
  "${RUNNER_ROOT}/service" \
  "${RUNNER_ROOT}/work"

DEPENDENCY_REPORT="${RUNNER_ROOT}/bootstrap_report.md"
SERVICE_TEMPLATE="${RUNNER_ROOT}/service/agentslam-runner.service"
ENV_TEMPLATE="${RUNNER_ROOT}/config/env.example"
README_PATH="${RUNNER_ROOT}/README.md"

check_dep() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    printf -- "- %s: present (%s)\n" "${name}" "$(command -v "${name}")"
  else
    printf -- "- %s: missing\n" "${name}"
  fi
}

cat >"${ENV_TEMPLATE}" <<EOF
# Example environment file for an AgentSlam runner service.
RUNNER_ROOT=${RUNNER_ROOT}
RUNNER_LABELS=${LABELS}
CODEX_HOME=/home/${SERVICE_USER}/.codex
REPO_ROOT=${ROOT_DIR}
EOF

cat >"${SERVICE_TEMPLATE}" <<EOF
[Unit]
Description=AgentSlam GitHub Actions Runner
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${RUNNER_ROOT}
EnvironmentFile=${RUNNER_ROOT}/config/env.example
ExecStart=${RUNNER_ROOT}/bin/run.sh
Restart=always
RestartSec=5
StandardOutput=append:${RUNNER_ROOT}/logs/runner.log
StandardError=append:${RUNNER_ROOT}/logs/runner.log

[Install]
WantedBy=multi-user.target
EOF

cat >"${README_PATH}" <<EOF
# AgentSlam Self-Hosted Runner Bootstrap

This scaffold was generated without performing any GitHub registration or tokenized setup.

Suggested labels:

- ${LABELS}

Key files:

- service template: \`${SERVICE_TEMPLATE}\`
- environment template: \`${ENV_TEMPLATE}\`
- bootstrap report: \`${DEPENDENCY_REPORT}\`

Next steps:

1. Read \`docs/SELF_HOSTED_RUNNER_SETUP.md\`.
2. Choose the real runner install root.
3. Download and register the GitHub runner manually in the GitHub UI.
4. Run \`codex login\` or \`codex login --device-auth\` as the runner user.
5. Enable the workflows after the runner labels match the repository docs.
EOF

cat >"${DEPENDENCY_REPORT}" <<EOF
# Self-Hosted Runner Bootstrap Report

- runner_root: \`${RUNNER_ROOT}\`
- service_user: \`${SERVICE_USER}\`
- labels: \`${LABELS}\`

## Dependency Check

$(check_dep bash)
$(check_dep git)
$(check_dep curl)
$(check_dep tar)
$(check_dep systemctl)
$(check_dep codex)
$(check_dep flock)

## Generated Files

- \`${README_PATH}\`
- \`${ENV_TEMPLATE}\`
- \`${SERVICE_TEMPLATE}\`

## Safety Notes

- no GitHub runner registration was performed
- no secrets or tokens were written
- no systemd service was installed automatically
EOF

cat <<EOF
self-hosted runner bootstrap scaffold created
- runner_root: ${RUNNER_ROOT}
- report: ${DEPENDENCY_REPORT}
- service_template: ${SERVICE_TEMPLATE}
EOF
