#!/usr/bin/env bash
# Clone or refresh AgentSlam reference repositories under refs/ without touching the main repo history.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REFS_DIR="${ROOT_DIR}/refs"
GITHUB_CLONE_PROTOCOL="${GITHUB_CLONE_PROTOCOL:-ssh}"

mkdir -p "${REFS_DIR}"

successes=()
failures=()

declare -a REPOS=(
  "IsaacSim-ros_workspaces|https://github.com/isaac-sim/IsaacSim-ros_workspaces.git|0"
  "navigation2|https://github.com/ros-navigation/navigation2.git|0"
  "slam_toolbox|https://github.com/SteveMacenski/slam_toolbox.git|0"
  "vision_opencv|https://github.com/ros-perception/vision_opencv.git|0"
  "message_filters|https://github.com/ros2/message_filters.git|0"
  "OneMap|https://github.com/KTH-RPL/OneMap.git|0"
  "HOV-SG|https://github.com/hovsg/HOV-SG.git|0"
  "concept-graphs|https://github.com/concept-graphs/concept-graphs.git|0"
  "DROID-SLAM|https://github.com/princeton-vl/DROID-SLAM.git|1"
  "MASt3R-SLAM|https://github.com/rmurai0610/MASt3R-SLAM.git|1"
  "GitNexus|https://github.com/abhigyanpatwari/GitNexus.git|0"
)

sync_repo() {
  local name="$1"
  local url="$2"
  local recursive="$3"
  local target="${REFS_DIR}/${name}"
  local effective_url="$url"

  if [[ "${GITHUB_CLONE_PROTOCOL}" == "ssh" && "${url}" == https://github.com/* ]]; then
    effective_url="git@github.com:${url#https://github.com/}"
  fi

  if [[ -d "${target}/.git" ]]; then
    echo "[fetch] ${name}"
    git -C "${target}" remote set-url origin "${effective_url}"
    git -C "${target}" fetch --all --tags --prune
    if [[ "${recursive}" == "1" ]]; then
      git -C "${target}" submodule sync --recursive
      git -C "${target}" submodule update --init --recursive
    fi
    return 0
  fi

  echo "[clone] ${name}"
  if [[ "${recursive}" == "1" ]]; then
    git clone --recursive "${effective_url}" "${target}"
  else
    git clone "${effective_url}" "${target}"
  fi
}

for repo_spec in "${REPOS[@]}"; do
  IFS="|" read -r name url recursive <<<"${repo_spec}"
  if sync_repo "${name}" "${url}" "${recursive}"; then
    successes+=("${name}")
  else
    failures+=("${name}")
    echo "[error] ${name} clone/fetch failed" >&2
  fi
done

echo "Reference repository sync complete: ${REFS_DIR}"
echo "Successful repositories: ${#successes[@]}"
for name in "${successes[@]}"; do
  echo "  - ${name}"
done

if [[ ${#failures[@]} -gt 0 ]]; then
  echo "Failed repositories: ${#failures[@]}" >&2
  for name in "${failures[@]}"; do
    echo "  - ${name}" >&2
  done
fi
