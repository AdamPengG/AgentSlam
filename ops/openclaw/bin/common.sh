#!/usr/bin/env bash
set -euo pipefail

agentslam_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd
}

openclaw_source_root() {
  printf '%s\n' "$(agentslam_root)/ops/openclaw"
}

openclaw_source_conf_root() {
  printf '%s\n' "$(openclaw_source_root)/src/conf.d"
}

openclaw_live_root() {
  printf '%s\n' "${OPENCLAW_HOME_OVERRIDE:-${HOME}/.openclaw}"
}

openclaw_timestamp() {
  date "+%Y%m%d-%H%M%S"
}

require_tool() {
  local tool_name="$1"
  if ! command -v "${tool_name}" >/dev/null 2>&1; then
    echo "required tool not found: ${tool_name}" >&2
    exit 1
  fi
}

openclaw_env_files() {
  local candidate
  for candidate in \
    "${HOME}/forGPT/SECRETS_OPENCLAW_LOCAL.env" \
    "${HOME}/forGPT/SECRETS_OPENCLAW_TELEGRAM.env"; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
    fi
  done
}

source_openclaw_service_env() {
  local env_line env_entry

  env_line="$(systemctl --user show openclaw-gateway.service -p Environment --value 2>/dev/null || true)"
  for env_entry in ${env_line}; do
    case "${env_entry}" in
      OPENCLAW_GATEWAY_TOKEN=*|OPENCLAW_GATEWAY_PORT=*|\
      http_proxy=*|https_proxy=*|all_proxy=*|no_proxy=*|\
      HTTP_PROXY=*|HTTPS_PROXY=*|ALL_PROXY=*|NO_PROXY=*|\
      NODE_USE_ENV_PROXY=*)
        export "${env_entry}"
        ;;
    esac
  done
}

source_openclaw_env() {
  local env_file
  while IFS= read -r env_file; do
    # shellcheck disable=SC1090
    source "${env_file}"
  done < <(openclaw_env_files)

  source_openclaw_service_env
}
