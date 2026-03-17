from __future__ import annotations

import argparse
import json
import struct
import sys
import time

import rclpy
from nav_msgs.msg import Odometry
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image, Imu
from std_msgs.msg import String

from .fixture_io import load_bridge_fixture, quaternion_from_yaw


class FixtureReplayPublisher(Node):
    """Publishes a minimal Phase 1 replay stream on standard ROS topics."""

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__("agentslam_fixture_replay_publisher")
        self.args = args
        self.scene = load_bridge_fixture(args.fixture)
        self.frame_index = 0
        self.finished_at: float | None = None
        self.should_exit = False
        self.publish_after = time.monotonic() + max(args.startup_delay_seconds, 0.0)

        self.rgb_pub = self.create_publisher(Image, args.rgb_topic, 10)
        self.depth_pub = self.create_publisher(Image, args.depth_topic, 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, args.camera_info_topic, 10)
        self.imu_pub = self.create_publisher(Imu, args.imu_topic, 10)
        self.pose_pub = self.create_publisher(Odometry, args.pose_topic, 10)
        self.detections_pub = self.create_publisher(String, args.detections_topic, 10)
        self.timer = self.create_timer(1.0 / max(args.playback_rate, 0.1), self._tick)

    def _tick(self) -> None:
        if time.monotonic() < self.publish_after:
            return
        if self.frame_index >= len(self.scene.frames):
            if self.args.loop:
                self.frame_index = 0
            else:
                if self.finished_at is None:
                    self.finished_at = time.monotonic()
                if time.monotonic() - self.finished_at >= self.args.linger_seconds:
                    self.get_logger().info("fixture replay complete")
                    self.should_exit = True
                return
        if self.args.wait_for_subscribers and not self._has_required_subscribers():
            return

        frame = self.scene.frames[self.frame_index]
        stamp = self.get_clock().now().to_msg()
        header_frame_id = self.args.camera_frame_id

        camera_info = CameraInfo()
        camera_info.header.stamp = stamp
        camera_info.header.frame_id = header_frame_id
        camera_info.width = self.args.image_width
        camera_info.height = self.args.image_height
        camera_info.k = [
            self.scene.intrinsics.fx,
            0.0,
            self.scene.intrinsics.cx,
            0.0,
            self.scene.intrinsics.fy,
            self.scene.intrinsics.cy,
            0.0,
            0.0,
            1.0,
        ]
        camera_info.p = [
            self.scene.intrinsics.fx,
            0.0,
            self.scene.intrinsics.cx,
            0.0,
            0.0,
            self.scene.intrinsics.fy,
            self.scene.intrinsics.cy,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
        ]
        self.camera_info_pub.publish(camera_info)

        rgb_image = Image()
        rgb_image.header.stamp = stamp
        rgb_image.header.frame_id = header_frame_id
        rgb_image.encoding = "rgb8"
        rgb_image.width = self.args.image_width
        rgb_image.height = self.args.image_height
        rgb_image.step = self.args.image_width * 3
        pixel = bytes([(30 + (self.frame_index * 40)) % 255, 100, 180])
        rgb_image.data = pixel * (self.args.image_width * self.args.image_height)
        self.rgb_pub.publish(rgb_image)

        depth_image = Image()
        depth_image.header.stamp = stamp
        depth_image.header.frame_id = header_frame_id
        depth_image.encoding = "32FC1"
        depth_image.width = self.args.image_width
        depth_image.height = self.args.image_height
        depth_image.step = self.args.image_width * 4
        nearest_depth = min(item.depth_m for item in frame.detections) if frame.detections else 3.0
        depth_image.data = struct.pack("<f", nearest_depth) * (self.args.image_width * self.args.image_height)
        self.depth_pub.publish(depth_image)

        imu_msg = Imu()
        imu_msg.header.stamp = stamp
        imu_msg.header.frame_id = self.args.imu_frame_id
        imu_msg.linear_acceleration.z = 9.81
        self.imu_pub.publish(imu_msg)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.args.world_frame_id
        odom.child_frame_id = self.args.base_frame_id
        odom.pose.pose.position.x = frame.pose.x
        odom.pose.pose.position.y = frame.pose.y
        odom.pose.pose.position.z = frame.pose.z
        qx, qy, qz, qw = quaternion_from_yaw(frame.pose.yaw)
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        self.pose_pub.publish(odom)

        detection_msg = String()
        detection_msg.data = json.dumps(
            {
                "frame_id": frame.frame_id,
                "source_mode": self.args.source_mode,
                "detections": [
                    {
                        "label": item.label,
                        "pixel_x": item.pixel_x,
                        "pixel_y": item.pixel_y,
                        "depth_m": item.depth_m,
                        "confidence": item.confidence,
                    }
                    for item in frame.detections
                ],
            }
        )
        self.detections_pub.publish(detection_msg)

        self.get_logger().info(f"published replay frame {frame.frame_id}")
        self.frame_index += 1

    def _has_required_subscribers(self) -> bool:
        return all(
            publisher.get_subscription_count() > 0
            for publisher in (
                self.camera_info_pub,
                self.pose_pub,
                self.detections_pub,
            )
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish a fixture as ROS topics for replay/live-smoke demos.")
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--playback-rate", type=float, default=2.0)
    parser.add_argument(
        "--startup-delay-seconds",
        type=float,
        default=0.0,
        help="Delay the first published frame to give subscribers time to connect.",
    )
    parser.add_argument("--loop", action="store_true")
    parser.add_argument(
        "--wait-for-subscribers",
        action="store_true",
        help="Do not publish the first frame until key subscribers are connected.",
    )
    parser.add_argument("--linger-seconds", type=float, default=1.5)
    parser.add_argument("--source-mode", default="bag_replay")
    parser.add_argument("--image-width", type=int, default=640)
    parser.add_argument("--image-height", type=int, default=480)
    parser.add_argument("--camera-frame-id", default="nova_camera_rgb")
    parser.add_argument("--imu-frame-id", default="nova_imu")
    parser.add_argument("--base-frame-id", default="nova_base_link")
    parser.add_argument("--world-frame-id", default="map")
    parser.add_argument("--camera-info-topic", default="/agentslam/camera/rgb/camera_info")
    parser.add_argument("--rgb-topic", default="/agentslam/camera/rgb/image_raw")
    parser.add_argument("--depth-topic", default="/agentslam/camera/depth/image_raw")
    parser.add_argument("--imu-topic", default="/agentslam/imu/data")
    parser.add_argument("--pose-topic", default="/agentslam/gt/odom")
    parser.add_argument("--detections-topic", default="/agentslam/semantic_detections")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rclpy.init(args=None)
    node = FixtureReplayPublisher(args)
    try:
        while rclpy.ok() and not node.should_exit:
            rclpy.spin_once(node, timeout_sec=0.1)
    except ExternalShutdownException:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
