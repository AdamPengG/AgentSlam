#!/usr/bin/env bash
# Discover local Isaac Sim launchers, Python entrypoints, and candidate office/robot/sensor assets.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAAC_INSTALL_HINT="${ISAAC_INSTALL_HINT:-/home/peng/IsaacSim}"
ISAAC_ASSET_ROOT="${ISAAC_ASSET_ROOT:-/home/peng/isaacsim_assets}"
MAX_RESULTS="${MAX_RESULTS:-30}"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

print_section() {
  local title="$1"
  printf '\n## %s\n\n' "${title}"
}

write_block_or_none() {
  local file_path="$1"
  if [[ -s "${file_path}" ]]; then
    sed "s#^#- #" "${file_path}"
  else
    echo "- none found"
  fi
}

collect_find() {
  local output_file="$1"
  shift
  if "$@" >"${output_file}" 2>/dev/null; then
    :
  else
    : >"${output_file}"
  fi
}

path_hits_file="${tmp_dir}/path_hits.txt"
entrypoints_file="${tmp_dir}/entrypoints.txt"
python_file="${tmp_dir}/python.txt"
office_file="${tmp_dir}/office.txt"
nova_file="${tmp_dir}/nova.txt"
wheeled_file="${tmp_dir}/wheeled.txt"
vision_file="${tmp_dir}/vision.txt"
imu_file="${tmp_dir}/imu.txt"

{
  command -v isaacsim || true
  command -v isaac-sim.sh || true
  command -v omniverse-launcher || true
} | sed '/^$/d' | sort -u >"${path_hits_file}"

if [[ -d "${ISAAC_INSTALL_HINT}" ]]; then
  collect_find "${entrypoints_file}" find "${ISAAC_INSTALL_HINT}" -maxdepth 5 -type f \
    \( -iname 'isaac-sim*.sh' -o -iname 'isaacsim*.sh' -o -iname '*.kit' -o -iname 'setup.sh' -o -iname 'repo.sh' \) \
    | sort | head -n "${MAX_RESULTS}"

  collect_find "${python_file}" find "${ISAAC_INSTALL_HINT}" -maxdepth 6 -type f \
    \( -iname 'python.sh' -o -iname 'python.bat' -o -iname '*python*.kit' \) \
    | sort | head -n "${MAX_RESULTS}"

  collect_find "${imu_file}" bash -lc "find '${ISAAC_INSTALL_HINT}' -maxdepth 8 \\( -type f -o -type d \\) | grep -E '(^|[^[:alpha:]])[Ii][Mm][Uu]([^[:alpha:]]|$)|Imu[A-Z]|IMU|inertial' | grep -Evi 'simulation|simulator' | sort | head -n '${MAX_RESULTS}'"
else
  : >"${entrypoints_file}"
  : >"${python_file}"
  : >"${imu_file}"
fi

if [[ -d "${ISAAC_ASSET_ROOT}" ]]; then
  collect_find "${office_file}" bash -lc "find '${ISAAC_ASSET_ROOT}' -maxdepth 8 -type f \\( -iname '*.usd' -o -iname '*.usda' \\) | grep -Ei '/Office/|office' | grep -Evi '/\\.thumbs/' | sort | head -n '${MAX_RESULTS}'"
  collect_find "${nova_file}" bash -lc "find '${ISAAC_ASSET_ROOT}' -maxdepth 8 -type f \\( -iname '*.usd' -o -iname '*.usda' \\) | grep -Ei 'nova_carter|nova_dev_kit|/Nova' | grep -Evi 'kinova' | sort | head -n '${MAX_RESULTS}'"
  collect_find "${wheeled_file}" bash -lc "find '${ISAAC_ASSET_ROOT}' -maxdepth 8 -type f \\( -iname '*.usd' -o -iname '*.usda' \\) | grep -Ei 'jackal|dingo|turtlebot|ridgeback|differential|wheeled|vehicle' | sort | head -n '${MAX_RESULTS}'"
  collect_find "${vision_file}" bash -lc "{ \
    find '${ISAAC_ASSET_ROOT}/Assets/Isaac' -maxdepth 6 \\( -path '*/Props/Camera/*' -o -path '*/Sensors/Intel/RealSense*' -o -path '*/Sensors/LeopardImaging/Hawk*' -o -path '*/Sensors/LeopardImaging/Owl*' -o -path '*/Sensors/Stereolabs/ZED_X*' -o -path '*/Sensors/Stereolabs/ZED_X_mini*' \\); \
    find '${ISAAC_ASSET_ROOT}' -maxdepth 8 -type f \\( -iname '*camera*.usd' -o -iname '*sensor*.usd' \\); \
  } | grep -Evi '/\\.thumbs/' | sort -u | head -n '${MAX_RESULTS}'"
else
  : >"${office_file}"
  : >"${nova_file}"
  : >"${wheeled_file}"
  : >"${vision_file}"
fi

echo "# Isaac Discovery"
echo
echo "- generated_from: \`${ROOT_DIR}/scripts/discover_isaac_assets.sh\`"
echo "- isaac_install_hint: \`${ISAAC_INSTALL_HINT}\`"
echo "- isaac_asset_root: \`${ISAAC_ASSET_ROOT}\`"

print_section "PATH Command Hits"
write_block_or_none "${path_hits_file}"

print_section "Candidate Isaac Launch And Setup Entrypoints"
write_block_or_none "${entrypoints_file}"

print_section "Candidate Isaac Python Entrypoints"
write_block_or_none "${python_file}"

print_section "Office Scene Candidate USDs"
write_block_or_none "${office_file}"

print_section "Nova Candidate USDs"
write_block_or_none "${nova_file}"

print_section "Fallback Wheeled Robot Candidate USDs"
write_block_or_none "${wheeled_file}"

print_section "Vision-Related Candidate Resources"
write_block_or_none "${vision_file}"

print_section "IMU-Related Candidate Resources"
write_block_or_none "${imu_file}"

print_section "Interpretation"
if [[ -s "${nova_file}" ]]; then
  echo '- a `nova`-named asset candidate was found locally'
else
  echo '- no `nova`-named USD asset was found in the searched asset tree'
fi
if [[ -s "${entrypoints_file}" ]]; then
  echo "- local Isaac install candidates exist, but no single launcher is treated as authoritative yet"
else
  echo "- no Isaac launcher candidates were found under the install hint"
fi
echo "- office assets are available locally if the searched Office USD set is representative"
echo '- Prompt 3 can proceed even if a definitive `nova` robot asset still requires upstream confirmation'
