#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


@dataclass
class Pose2D:
    x: float
    y: float
    yaw_rad: float


def wrap_angle(angle: float) -> float:
    return math.atan2(math.sin(angle), math.cos(angle))


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


class WaypointFollower(Node):
    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("agentslam_waypoint_follower")
        self.args = args
        payload = json.loads(Path(args.path_json).read_text(encoding="utf-8"))
        self.local_waypoints = [(float(p["x"]), float(p["y"])) for p in payload["waypoints_local_start_frame"]]
        if len(self.local_waypoints) < 2:
            raise RuntimeError("path json does not contain enough waypoints")

        self.cmd_pub = self.create_publisher(Twist, args.cmd_topic, 10)
        self.create_subscription(Odometry, args.odom_topic, self._on_odom, 50)
        self.timer = self.create_timer(1.0 / args.control_rate_hz, self._on_timer)

        self.start_pose: Pose2D | None = None
        self.current_pose: Pose2D | None = None
        self.global_waypoints: list[tuple[float, float]] = []
        self.current_index = 1
        self.completed = False
        self.timed_out = False
        self.should_exit = False
        self.start_time = time.monotonic()
        self.reached_final_time: float | None = None
        self.path_length_m = self._compute_local_path_length()

    def _compute_local_path_length(self) -> float:
        length = 0.0
        for index in range(len(self.local_waypoints) - 1):
            dx = self.local_waypoints[index + 1][0] - self.local_waypoints[index][0]
            dy = self.local_waypoints[index + 1][1] - self.local_waypoints[index][1]
            length += math.hypot(dx, dy)
        return length

    def _on_odom(self, msg: Odometry) -> None:
        pose = msg.pose.pose
        current = Pose2D(
            x=float(pose.position.x),
            y=float(pose.position.y),
            yaw_rad=quaternion_to_yaw(
                float(pose.orientation.x),
                float(pose.orientation.y),
                float(pose.orientation.z),
                float(pose.orientation.w),
            ),
        )
        self.current_pose = current
        if self.start_pose is None:
            self.start_pose = current
            self.global_waypoints = [(self.start_pose.x + x, self.start_pose.y + y) for x, y in self.local_waypoints]

    def _publish_stop(self) -> None:
        msg = Twist()
        self.cmd_pub.publish(msg)

    def _mark_complete(self) -> None:
        if not self.completed:
            self.completed = True
            self.reached_final_time = time.monotonic()
            self._publish_stop()

    def _on_timer(self) -> None:
        if self.completed:
            self._publish_stop()
            if self.reached_final_time is not None and time.monotonic() - self.reached_final_time > 1.0:
                self.should_exit = True
            return
        if self.current_pose is None or not self.global_waypoints:
            return
        if time.monotonic() - self.start_time > self.args.timeout_seconds:
            self.get_logger().warning("path follower timed out before reaching the final waypoint")
            self.timed_out = True
            self._publish_stop()
            self.should_exit = True
            return

        while self.current_index < len(self.global_waypoints) - 1:
            target_x, target_y = self.global_waypoints[self.current_index]
            if math.hypot(target_x - self.current_pose.x, target_y - self.current_pose.y) <= self.args.waypoint_tolerance_m:
                self.current_index += 1
            else:
                break

        goal_x, goal_y = self.global_waypoints[-1]
        goal_distance = math.hypot(goal_x - self.current_pose.x, goal_y - self.current_pose.y)
        if goal_distance <= self.args.goal_tolerance_m:
            self._mark_complete()
            return

        target_x, target_y = self.global_waypoints[self.current_index]
        target_heading = math.atan2(target_y - self.current_pose.y, target_x - self.current_pose.x)
        heading_error = wrap_angle(target_heading - self.current_pose.yaw_rad)

        twist = Twist()
        if abs(heading_error) > self.args.forward_angle_threshold_rad:
            twist.linear.x = 0.0
        else:
            slow_down = min(1.0, max(goal_distance / max(self.args.goal_slowdown_distance_m, 1e-3), 0.2))
            twist.linear.x = float(self.args.linear_speed_mps * slow_down)
        twist.angular.z = float(
            max(-self.args.max_angular_speed_radps, min(self.args.max_angular_speed_radps, self.args.angular_gain * heading_error))
        )
        self.cmd_pub.publish(twist)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Follow a planned waypoint path using a simple pure-pursuit-like controller.")
    parser.add_argument("--path-json", required=True)
    parser.add_argument("--odom-topic", default="/chassis/odom")
    parser.add_argument("--cmd-topic", default="/cmd_vel")
    parser.add_argument("--runtime-output", required=True)
    parser.add_argument("--control-rate-hz", type=float, default=10.0)
    parser.add_argument("--linear-speed-mps", type=float, default=0.25)
    parser.add_argument("--angular-gain", type=float, default=1.8)
    parser.add_argument("--max-angular-speed-radps", type=float, default=1.0)
    parser.add_argument("--forward-angle-threshold-rad", type=float, default=1.1)
    parser.add_argument("--waypoint-tolerance-m", type=float, default=0.25)
    parser.add_argument("--goal-tolerance-m", type=float, default=0.20)
    parser.add_argument("--goal-slowdown-distance-m", type=float, default=1.0)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runtime_path = Path(args.runtime_output)
    runtime_path.parent.mkdir(parents=True, exist_ok=True)

    rclpy.init()
    node = WaypointFollower(args)
    start = time.monotonic()
    try:
        while rclpy.ok() and not node.should_exit:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        pass
    except Exception as exc:
        if "context is not valid" not in str(exc):
            raise
    finally:
        runtime = {
            "path_json": str(Path(args.path_json).resolve()),
            "odom_topic": args.odom_topic,
            "cmd_topic": args.cmd_topic,
            "completed": bool(node.completed),
            "timed_out": bool(node.timed_out),
            "current_waypoint_index": int(node.current_index),
            "path_length_m": float(node.path_length_m),
            "duration_seconds": float(time.monotonic() - start),
            "start_pose": None
            if node.start_pose is None
            else {"x": node.start_pose.x, "y": node.start_pose.y, "yaw_rad": node.start_pose.yaw_rad},
            "final_pose": None
            if node.current_pose is None
            else {"x": node.current_pose.x, "y": node.current_pose.y, "yaw_rad": node.current_pose.yaw_rad},
        }
        runtime_path.write_text(json.dumps(runtime, indent=2) + "\n", encoding="utf-8")
        if rclpy.ok():
            node._publish_stop()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0 if node.completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
