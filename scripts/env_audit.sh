#!/usr/bin/env bash
# Audit the local development environment for Prompt 2 prerequisites and print a markdown report.
set -euo pipefail

tool_total=11
available_count=0
missing_tools=()

run_version() {
  local cmd="$1"
  bash -lc "${cmd}" 2>/dev/null | head -n 1 || true
}

emit_row() {
  local tool="$1"
  local status="$2"
  local path="$3"
  local version="$4"
  printf '| %s | %s | `%s` | %s |\n' "${tool}" "${status}" "${path}" "${version}"
}

check_tool() {
  local tool="$1"
  local path=""
  local version="not available"
  local status="missing"

  case "${tool}" in
    git)
      path="$(command -v git || true)"
      [[ -n "${path}" ]] && version="$(run_version 'git --version')"
      ;;
    python3)
      path="$(command -v python3 || true)"
      [[ -n "${path}" ]] && version="$(run_version 'python3 --version')"
      ;;
    pip)
      path="$(command -v pip || true)"
      if [[ -n "${path}" ]]; then
        version="$(run_version 'pip --version')"
      elif command -v python3 >/dev/null 2>&1; then
        path="$(command -v python3)"
        version="$(run_version 'python3 -m pip --version')"
      fi
      ;;
    npm)
      path="$(command -v npm || true)"
      [[ -n "${path}" ]] && version="$(run_version 'npm --version')"
      ;;
    npx)
      path="$(command -v npx || true)"
      [[ -n "${path}" ]] && version="$(run_version 'npx --version')"
      ;;
    docker)
      path="$(command -v docker || true)"
      [[ -n "${path}" ]] && version="$(run_version 'docker --version')"
      ;;
    colcon)
      path="$(command -v colcon || true)"
      if [[ -n "${path}" ]]; then
        version="$(run_version 'colcon --version')"
        [[ -z "${version}" ]] && version="$(run_version 'colcon --help')"
      fi
      ;;
    ros2)
      path="$(command -v ros2 || true)"
      [[ -n "${path}" ]] && version="$(run_version 'ros2 --help')"
      ;;
    cmake)
      path="$(command -v cmake || true)"
      [[ -n "${path}" ]] && version="$(run_version 'cmake --version')"
      ;;
    gcc)
      path="$(command -v gcc || true)"
      [[ -n "${path}" ]] && version="$(run_version 'gcc --version')"
      ;;
    git-lfs)
      path="$(command -v git-lfs || true)"
      if [[ -n "${path}" ]]; then
        version="$(run_version 'git-lfs --version')"
      elif command -v git >/dev/null 2>&1 && git lfs version >/dev/null 2>&1; then
        path="$(command -v git)"
        version="$(run_version 'git lfs version')"
      fi
      ;;
  esac

  if [[ -n "${path}" ]]; then
    status="available"
    available_count=$((available_count + 1))
  else
    path="n/a"
    missing_tools+=("${tool}")
  fi

  emit_row "${tool}" "${status}" "${path}" "${version}"
}

echo "# Environment Audit"
echo
echo "- generated_from: \`scripts/env_audit.sh\`"
echo
echo "| Tool | Status | Path | Version |"
echo "| --- | --- | --- | --- |"

check_tool git
check_tool python3
check_tool pip
check_tool npm
check_tool npx
check_tool docker
check_tool colcon
check_tool ros2
check_tool cmake
check_tool gcc
check_tool git-lfs

echo
echo "## Summary"
echo
echo "- available_tools: ${available_count}/${tool_total}"
if [[ ${#missing_tools[@]} -eq 0 ]]; then
  echo "- missing_tools: none"
else
  printf -- '- missing_tools: %s\n' "$(IFS=', '; echo "${missing_tools[*]}")"
fi

echo
echo "## Notes"
echo
if [[ ! -x "$(command -v ros2 || true)" && -d /opt/ros ]]; then
  echo "- ROS 2 may be installed but not sourced in the current shell. Detected distros:"
  ls -1 /opt/ros | sed 's#^#  - #' || true
fi
if [[ ! -x "$(command -v colcon || true)" && -d /opt/ros ]]; then
  echo "- `colcon` is not on PATH in this shell. If ROS 2 is installed, source its setup before retrying."
fi
echo "- This report captures shell availability only; it does not validate runtime permissions for Docker or ROS graph access."
