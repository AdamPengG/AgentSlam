#!/usr/bin/env bash
# Validate and optionally prepare the preferred Isaac Phase 1 Office + Nova entrypoint.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISAAC_LAUNCHER="${ISAAC_LAUNCHER:-/home/peng/IsaacSim/_build/linux-x86_64/release/isaac-sim.sh}"
ISAAC_PYTHON="${ISAAC_PYTHON:-/home/peng/IsaacSim/_build/linux-x86_64/release/python.sh}"
OFFICE_SCENE="${OFFICE_SCENE:-/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd}"
NOVA_ROBOT="${NOVA_ROBOT:-/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd}"
SUMMARY_PATH="${ROOT_DIR}/artifacts/phase1/office_nova_isaac_validation.json"
MODE="${1:---validate-only}"

mkdir -p "${ROOT_DIR}/artifacts/phase1"

if [[ ! -x "${ISAAC_LAUNCHER}" ]]; then
  echo "missing Isaac launcher: ${ISAAC_LAUNCHER}" >&2
  exit 1
fi
if [[ ! -x "${ISAAC_PYTHON}" ]]; then
  echo "missing Isaac python entrypoint: ${ISAAC_PYTHON}" >&2
  exit 1
fi
if [[ ! -f "${OFFICE_SCENE}" ]]; then
  echo "missing office scene USD: ${OFFICE_SCENE}" >&2
  exit 1
fi
if [[ ! -f "${NOVA_ROBOT}" ]]; then
  echo "missing Nova Carter USD: ${NOVA_ROBOT}" >&2
  exit 1
fi

timeout "${ISAAC_VALIDATE_TIMEOUT:-180s}" bash "${ISAAC_PYTHON}" \
  "${ROOT_DIR}/scripts/validate_isaac_office_nova_scene.py" \
  --scene "${OFFICE_SCENE}" \
  --robot "${NOVA_ROBOT}" \
  --output-json "${SUMMARY_PATH}"

cat <<EOF
validated Isaac release entrypoints and Office + Nova asset pairing
- launcher: ${ISAAC_LAUNCHER}
- python: ${ISAAC_PYTHON}
- office_scene: ${OFFICE_SCENE}
- nova_robot: ${NOVA_ROBOT}
- summary: ${SUMMARY_PATH}
EOF

if [[ "${MODE}" == "--print-live-command" ]]; then
  cat <<EOF
preferred live launcher template:
bash "${ISAAC_LAUNCHER}"
EOF
fi
