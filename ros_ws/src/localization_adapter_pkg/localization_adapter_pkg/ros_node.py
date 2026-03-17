from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

import rclpy
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String

from .core import build_status_payload, choose_active_source


class LocalizationAdapterNode(Node):
    """Normalizes localization output so mapping and semantics consume one odom topic."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("agentslam_localization_adapter")
        self.args = args
        self.runtime_output = Path(args.runtime_output) if args.runtime_output else None

        self.latest_primary: Odometry | None = None
        self.latest_primary_at: float | None = None
        self.latest_fallback: Odometry | None = None
        self.latest_fallback_at: float | None = None
        self.active_source: str | None = None
        self.last_publish_time: float | None = None

        self.metrics = {
            "primary_messages": 0,
            "fallback_messages": 0,
            "published_messages": 0,
            "active_source_switches": 0,
        }

        self.odom_pub = self.create_publisher(Odometry, args.output_odom_topic, 10)
        self.status_pub = self.create_publisher(String, args.status_topic, 10)
        self.create_subscription(Odometry, args.primary_odom_topic, self._on_primary_odom, 10)
        self.create_subscription(Odometry, args.fallback_odom_topic, self._on_fallback_odom, 10)
        self.create_timer(1.0 / max(args.publish_rate_hz, 1.0), self._publish_selected_odom)

    def _on_primary_odom(self, msg: Odometry) -> None:
        self.latest_primary = copy.deepcopy(msg)
        self.latest_primary_at = time.monotonic()
        self.metrics["primary_messages"] += 1
        self._publish_selected_odom()

    def _on_fallback_odom(self, msg: Odometry) -> None:
        self.latest_fallback = copy.deepcopy(msg)
        self.latest_fallback_at = time.monotonic()
        self.metrics["fallback_messages"] += 1
        self._publish_selected_odom()

    def _publish_selected_odom(self) -> None:
        now = time.monotonic()
        primary_age_s = None if self.latest_primary_at is None else now - self.latest_primary_at
        selected_source = choose_active_source(
            primary_age_s=primary_age_s,
            fallback_available=self.latest_fallback is not None,
            primary_timeout_s=self.args.primary_timeout_s,
        )
        if selected_source is None:
            return

        if selected_source != self.active_source:
            if self.active_source is not None:
                self.metrics["active_source_switches"] += 1
            self.active_source = selected_source

        selected_msg = self.latest_primary if selected_source == "primary" else self.latest_fallback
        if selected_msg is None:
            return

        self.odom_pub.publish(copy.deepcopy(selected_msg))
        self.metrics["published_messages"] += 1
        self.last_publish_time = now

        status = String()
        status.data = json.dumps(
            build_status_payload(
                active_source=self.active_source,
                primary_topic=self.args.primary_odom_topic,
                fallback_topic=self.args.fallback_odom_topic,
                output_topic=self.args.output_odom_topic,
                primary_messages=self.metrics["primary_messages"],
                fallback_messages=self.metrics["fallback_messages"],
                primary_age_s=primary_age_s,
            )
        )
        self.status_pub.publish(status)

    def finalize(self) -> None:
        if self.runtime_output is None:
            return
        self.runtime_output.parent.mkdir(parents=True, exist_ok=True)
        primary_age_s = None
        if self.latest_primary_at is not None:
            primary_age_s = time.monotonic() - self.latest_primary_at
        payload = {
            **self.metrics,
            "active_source": self.active_source or "none",
            "primary_topic": self.args.primary_odom_topic,
            "fallback_topic": self.args.fallback_odom_topic,
            "output_odom_topic": self.args.output_odom_topic,
            "status_topic": self.args.status_topic,
            "primary_timeout_s": self.args.primary_timeout_s,
            "last_publish_time_set": self.last_publish_time is not None,
        }
        if primary_age_s is not None:
            payload["primary_age_s"] = round(primary_age_s, 4)
        self.runtime_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select a localization odometry source with primary/fallback semantics."
    )
    parser.add_argument(
        "--primary-odom-topic",
        default="/visual_slam/tracking/odometry",
        help="Preferred odometry source, typically a visual SLAM backend.",
    )
    parser.add_argument(
        "--fallback-odom-topic",
        default="/agentslam/gt/odom",
        help="Fallback odometry source used while the preferred source is unavailable.",
    )
    parser.add_argument(
        "--output-odom-topic",
        default="/agentslam/localization/odom",
        help="Normalized localization topic consumed by mapping and semantic nodes.",
    )
    parser.add_argument(
        "--status-topic",
        default="/agentslam/localization/status",
        help="JSON status topic describing which odometry source is active.",
    )
    parser.add_argument(
        "--primary-timeout-s",
        type=float,
        default=0.75,
        help="If the preferred source is older than this, fall back to the backup odometry stream.",
    )
    parser.add_argument(
        "--publish-rate-hz",
        type=float,
        default=10.0,
        help="Republish rate for the normalized localization output.",
    )
    parser.add_argument(
        "--runtime-output",
        help="Optional path for a runtime summary JSON written on shutdown.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rclpy.init(args=None)
    node = LocalizationAdapterNode(args)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.finalize()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
