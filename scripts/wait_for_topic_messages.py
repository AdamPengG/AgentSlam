#!/usr/bin/env python3
"""Wait until each requested ROS topic has delivered at least one message."""

from __future__ import annotations

import argparse
import sys
import time
from functools import partial

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from rosidl_runtime_py.utilities import get_message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument(
        "--expect",
        action="append",
        nargs=2,
        metavar=("TOPIC", "MSG_TYPE"),
        required=True,
        help="Topic name and ROS message type to wait for.",
    )
    return parser.parse_args()


class WaitForTopicMessages(Node):
    def __init__(self, expectations: list[tuple[str, str]]) -> None:
        super().__init__("agentslam_wait_for_topic_messages")
        self.received: dict[str, bool] = {}
        self._message_subscriptions = []
        for topic, msg_type_name in expectations:
            self.received[topic] = False
            msg_type = get_message(msg_type_name)
            qos = self._qos_for_topic(topic)
            subscription = self.create_subscription(
                msg_type,
                topic,
                partial(self._on_message, topic),
                qos,
            )
            self._message_subscriptions.append(subscription)

    @staticmethod
    def _qos_for_topic(topic: str) -> QoSProfile:
        if topic == "/tf_static":
            return QoSProfile(
                depth=10,
                durability=DurabilityPolicy.TRANSIENT_LOCAL,
                reliability=ReliabilityPolicy.RELIABLE,
            )
        return QoSProfile(depth=10)

    def _on_message(self, topic: str, _msg) -> None:
        self.received[topic] = True

    def all_received(self) -> bool:
        return all(self.received.values())

    def missing_topics(self) -> list[str]:
        return sorted(topic for topic, seen in self.received.items() if not seen)


def main() -> int:
    args = parse_args()
    expectations = [(topic, msg_type) for topic, msg_type in args.expect]
    deadline = time.monotonic() + max(args.timeout_seconds, 0.1)

    rclpy.init(args=[])
    node = WaitForTopicMessages(expectations)
    try:
        while rclpy.ok() and time.monotonic() < deadline:
            if node.all_received():
                return 0
            rclpy.spin_once(node, timeout_sec=0.1)
        print("\n".join(node.missing_topics()), file=sys.stderr)
        return 1
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
