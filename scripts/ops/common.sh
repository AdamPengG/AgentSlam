#!/usr/bin/env bash

agentslam_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd
}

ops_timestamp() {
  date "+%Y%m%d-%H%M%S"
}

latest_matching_file() {
  local pattern="$1"
  local matches=()
  local result=""

  shopt -s nullglob
  matches=(${pattern})
  shopt -u nullglob

  if [[ ${#matches[@]} -eq 0 ]]; then
    return 1
  fi

  result="$(ls -1t "${matches[@]}" 2>/dev/null | head -n 1)"
  [[ -n "${result}" ]] || return 1
  printf '%s\n' "${result}"
}

copy_if_exists() {
  local source_path="$1"
  local dest_path="$2"

  if [[ -e "${source_path}" ]]; then
    mkdir -p "$(dirname "${dest_path}")"
    cp -f "${source_path}" "${dest_path}"
    return 0
  fi

  return 1
}

latest_matching_file_excluding() {
  local pattern="$1"
  local exclude_path="$2"
  local matches=()
  local candidate=""

  shopt -s nullglob
  matches=(${pattern})
  shopt -u nullglob

  if [[ ${#matches[@]} -eq 0 ]]; then
    return 1
  fi

  while IFS= read -r candidate; do
    if [[ "${candidate}" != "${exclude_path}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done < <(ls -1t "${matches[@]}" 2>/dev/null)

  return 1
}

sha256_of_file() {
  local file_path="$1"
  sha256sum "${file_path}" | awk '{print $1}'
}
