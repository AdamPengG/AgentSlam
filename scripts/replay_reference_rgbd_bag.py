#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    from rosbags.highlevel import AnyReader
except ImportError as exc:  # pragma: no cover - exercised in operator environments
    raise SystemExit(
        "missing Python package 'rosbags'; install with `/usr/bin/python3 -m pip install --user rosbags`"
    ) from exc

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


class ReferenceBagReplayNode(Node):
    """Replay selected RGBD rosbag topics into the current ROS graph."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("agentslam_reference_rgbd_replay")
        self.args = args
        self.remaps = dict(item.split(":=", 1) for item in args.remap)

        bag_path = Path(args.bag)
        if not bag_path.exists():
            raise SystemExit(f"missing bag path: {bag_path}")
        self.reader = AnyReader([bag_path])
        self.reader.open()

        self.connections = [
            connection
            for connection in self.reader.connections
            if connection.topic in self.remaps
        ]
        if not self.connections:
            available = ", ".join(sorted(connection.topic for connection in self.reader.connections))
            raise SystemExit(
                f"no requested topics found in bag; available topics: {available}"
            )

        self.topic_publishers = {}
        self.message_classes = {}
        for connection in self.connections:
            msg_cls = get_message(connection.msgtype)
            self.message_classes[connection.id] = msg_cls
            qos_profile = qos_from_connection(connection)
            self.topic_publishers[connection.id] = self.create_publisher(
                msg_cls,
                self.remaps[connection.topic],
                qos_profile,
            )

    def replay(self) -> None:
        start_time = time.monotonic() + max(self.args.start_delay_seconds, 0.0)
        first_stamp_ns: int | None = None

        for connection, timestamp, rawdata in self.reader.messages(connections=self.connections):
            if first_stamp_ns is None:
                first_stamp_ns = timestamp

            elapsed_s = 0.0
            if first_stamp_ns is not None:
                elapsed_s = max(timestamp - first_stamp_ns, 0) / 1e9 / max(self.args.rate, 0.01)
            target_time = start_time + elapsed_s
            while True:
                remaining = target_time - time.monotonic()
                if remaining <= 0.0:
                    break
                time.sleep(min(remaining, 0.05))

            msg_cls = self.message_classes[connection.id]
            publisher = self.topic_publishers[connection.id]
            publisher.publish(deserialize_message(rawdata, msg_cls))

        linger_until = time.monotonic() + max(self.args.linger_seconds, 0.0)
        while time.monotonic() < linger_until:
            time.sleep(0.05)

    def close(self) -> None:
        self.reader.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay selected RGBD rosbag topics without requiring ros2 bag MCAP support."
    )
    parser.add_argument("--bag", required=True, help="Path to the rosbag directory.")
    parser.add_argument(
        "--remap",
        action="append",
        required=True,
        help="Topic remap in src:=dst form. Repeat for each topic to replay.",
    )
    parser.add_argument("--rate", type=float, default=1.0, help="Playback rate multiplier.")
    parser.add_argument(
        "--start-delay-seconds",
        type=float,
        default=1.0,
        help="Delay before publishing the first message.",
    )
    parser.add_argument(
        "--linger-seconds",
        type=float,
        default=1.0,
        help="How long to keep the node alive after the final message.",
    )
    return parser.parse_args(argv)


def qos_from_connection(connection) -> QoSProfile:
    profiles = getattr(connection.ext, "offered_qos_profiles", None)
    if not profiles:
        return QoSProfile(depth=10)

    profile = profiles[0]
    depth = profile.depth if getattr(profile, "depth", 0) > 0 else 10
    qos_profile = QoSProfile(depth=depth)
    qos_profile.history = HistoryPolicy.KEEP_LAST
    qos_profile.reliability = (
        ReliabilityPolicy.BEST_EFFORT
        if getattr(profile, "reliability", None).name == "BEST_EFFORT"
        else ReliabilityPolicy.RELIABLE
    )
    qos_profile.durability = (
        DurabilityPolicy.TRANSIENT_LOCAL
        if getattr(profile, "durability", None).name == "TRANSIENT_LOCAL"
        else DurabilityPolicy.VOLATILE
    )
    return qos_profile


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rclpy.init(args=[])
    node = ReferenceBagReplayNode(args)
    try:
        node.replay()
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
