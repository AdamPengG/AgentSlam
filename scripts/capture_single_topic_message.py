#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from rosidl_runtime_py.convert import message_to_ordereddict
from rosidl_runtime_py.utilities import get_message


class SingleMessageCaptureNode(Node):
    """Capture one ROS message and persist it as JSON."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("agentslam_single_message_capture")
        self.args = args
        self.output_path = Path(args.output)
        self.received = False
        self.subscription = self.create_subscription(
            get_message(args.msg_type),
            args.topic,
            self._on_message,
            10,
        )

    def _on_message(self, msg) -> None:
        if self.received:
            return
        self.received = True
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(
            json.dumps(message_to_ordereddict(msg), indent=2),
            encoding="utf-8",
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture one ROS message and write it to disk as JSON.")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--msg-type", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rclpy.init(args=[])
    node = SingleMessageCaptureNode(args)
    deadline = time.monotonic() + max(args.timeout_seconds, 0.1)
    try:
        while rclpy.ok() and not node.received and time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0 if node.received else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
