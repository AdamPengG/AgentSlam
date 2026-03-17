#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: agentslam_build.sh [--dry-run] [--packages "pkg1 pkg2 ..."]

Run the package-scoped AgentSlam build through a serialized wrapper and log the
result under artifacts/ops/openclaw/build/.
EOF
}

ROOT_DIR="/home/peng/AgentSlam"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_DIR="${ROOT_DIR}/artifacts/ops/openclaw/build/${STAMP}"
LOG_PATH="${LOG_DIR}/colcon_build.log"
PACKAGES="sim_bridge_pkg semantic_mapper_pkg room_graph_pkg semantic_query_pkg nav2_overlay_pkg localization_adapter_pkg eval_tools_pkg"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --packages)
      PACKAGES="$2"
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

mkdir -p "${LOG_DIR}"
BUILD_CMD="set +u; source /opt/ros/humble/setup.bash; set -u; cd '${ROOT_DIR}/ros_ws'; colcon build --packages-select ${PACKAGES}"

if [[ ${DRY_RUN} -eq 1 ]]; then
  echo "${BUILD_CMD}"
  exit 0
fi

bash "${ROOT_DIR}/ops/openclaw/bin/agentslam_lock.sh" --name agentslam-build -- \
  bash -lc "${BUILD_CMD}" >"${LOG_PATH}" 2>&1

echo "build_log=${LOG_PATH}"
