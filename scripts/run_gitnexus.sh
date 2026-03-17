#!/usr/bin/env bash
# Run GitNexus CLI from the repository root with an explicit npx-based fallback path.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <analyze|status|query|context|impact> [args...]" >&2
  exit 1
fi

cd "${ROOT_DIR}"
npx -y gitnexus@latest "$@"
