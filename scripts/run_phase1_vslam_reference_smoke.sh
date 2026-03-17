#!/usr/bin/env bash
set -euo pipefail

echo "scripts/run_phase1_vslam_reference_smoke.sh is deprecated." >&2
echo "The current GS4-hosted isaac_ros_visual_slam backend expects the live stereo contract, not the earlier RGBD trial." >&2
echo "Use scripts/run_phase1_vslam_live_stereo_smoke.sh instead." >&2
exit 2
