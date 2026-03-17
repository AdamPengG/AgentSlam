#!/usr/bin/env python3
"""Wait until all requested ROS topics are visible using rclpy directly."""

from __future__ import annotations

import argparse
import sys
import time

import rclpy
from rclpy.node import Node


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("topics", nargs="+")
    args = parser.parse_args()

    deadline = time.time() + max(0.0, args.timeout_seconds)
    expected = set(args.topics)

    rclpy.init(args=[])
    node = Node("agentslam_wait_for_topics")
    try:
        while time.time() <= deadline:
            seen = {name for name, _ in node.get_topic_names_and_types()}
            missing = expected - seen
            if not missing:
                return 0
            time.sleep(0.2)
        print("\n".join(sorted(missing)), file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
