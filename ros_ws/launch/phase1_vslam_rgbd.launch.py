from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description() -> LaunchDescription:
    rgb_topic = LaunchConfiguration("rgb_topic")
    camera_info_topic = LaunchConfiguration("camera_info_topic")
    depth_topic = LaunchConfiguration("depth_topic")
    base_frame = LaunchConfiguration("base_frame")
    depth_scale_factor = LaunchConfiguration("depth_scale_factor")
    use_sim_time = LaunchConfiguration("use_sim_time")
    enable_slam_visualization = LaunchConfiguration("enable_slam_visualization")
    enable_landmarks_view = LaunchConfiguration("enable_landmarks_view")
    enable_observations_view = LaunchConfiguration("enable_observations_view")

    visual_slam_node = ComposableNode(
        name="visual_slam_node",
        package="isaac_ros_visual_slam",
        plugin="nvidia::isaac_ros::visual_slam::VisualSlamNode",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "tracking_mode": 2,
                "depth_scale_factor": depth_scale_factor,
                "rectified_images": False,
                "image_jitter_threshold_ms": 30.0,
                "sync_matching_threshold_ms": 10.0,
                "base_frame": base_frame,
                "enable_slam_visualization": enable_slam_visualization,
                "enable_landmarks_view": enable_landmarks_view,
                "enable_observations_view": enable_observations_view,
                "enable_ground_constraint_in_odometry": False,
                "enable_ground_constraint_in_slam": False,
                "enable_localization_n_mapping": True,
                "min_num_images": 1,
                "num_cameras": 1,
                "depth_camera_id": 0,
            }
        ],
        remappings=[
            ("visual_slam/image_0", rgb_topic),
            ("visual_slam/camera_info_0", camera_info_topic),
            ("visual_slam/depth_0", depth_topic),
        ],
    )

    visual_slam_container = ComposableNodeContainer(
        name="agentslam_visual_slam_container",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        composable_node_descriptions=[visual_slam_node],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("rgb_topic", default_value="/agentslam/camera/rgb/image_raw"),
            DeclareLaunchArgument(
                "camera_info_topic",
                default_value="/agentslam/camera/rgb/camera_info",
            ),
            DeclareLaunchArgument("depth_topic", default_value="/agentslam/camera/depth/image_raw"),
            DeclareLaunchArgument("base_frame", default_value="nova_base_link"),
            DeclareLaunchArgument("depth_scale_factor", default_value="1.0"),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("enable_slam_visualization", default_value="false"),
            DeclareLaunchArgument("enable_landmarks_view", default_value="false"),
            DeclareLaunchArgument("enable_observations_view", default_value="false"),
            visual_slam_container,
        ]
    )
