from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description() -> LaunchDescription:
    left_image_topic = LaunchConfiguration("left_image_topic")
    left_camera_info_topic = LaunchConfiguration("left_camera_info_topic")
    right_image_topic = LaunchConfiguration("right_image_topic")
    right_camera_info_topic = LaunchConfiguration("right_camera_info_topic")
    use_sim_time = LaunchConfiguration("use_sim_time")
    enable_image_denoising = LaunchConfiguration("enable_image_denoising")
    rectified_images = LaunchConfiguration("rectified_images")
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
                "enable_image_denoising": enable_image_denoising,
                "rectified_images": rectified_images,
                "enable_slam_visualization": enable_slam_visualization,
                "enable_landmarks_view": enable_landmarks_view,
                "enable_observations_view": enable_observations_view,
            }
        ],
        remappings=[
            ("visual_slam/image_0", left_image_topic),
            ("visual_slam/camera_info_0", left_camera_info_topic),
            ("visual_slam/image_1", right_image_topic),
            ("visual_slam/camera_info_1", right_camera_info_topic),
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
            DeclareLaunchArgument(
                "left_image_topic",
                default_value="/front_stereo_camera/left/image_rect_color",
            ),
            DeclareLaunchArgument(
                "left_camera_info_topic",
                default_value="/front_stereo_camera/left/camera_info",
            ),
            DeclareLaunchArgument(
                "right_image_topic",
                default_value="/front_stereo_camera/right/image_rect_color",
            ),
            DeclareLaunchArgument(
                "right_camera_info_topic",
                default_value="/front_stereo_camera/right/camera_info",
            ),
            DeclareLaunchArgument("use_sim_time", default_value="false"),
            DeclareLaunchArgument("enable_image_denoising", default_value="true"),
            DeclareLaunchArgument("rectified_images", default_value="true"),
            DeclareLaunchArgument("enable_slam_visualization", default_value="false"),
            DeclareLaunchArgument("enable_landmarks_view", default_value="false"),
            DeclareLaunchArgument("enable_observations_view", default_value="false"),
            visual_slam_container,
        ]
    )
