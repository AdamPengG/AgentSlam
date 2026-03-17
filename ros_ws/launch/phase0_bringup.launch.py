from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration


def generate_launch_description() -> LaunchDescription:
    isaac_launcher = LaunchConfiguration("isaac_launcher")
    scene_usd = LaunchConfiguration("scene_usd")
    robot_usd = LaunchConfiguration("robot_usd")
    use_mock_streams = LaunchConfiguration("use_mock_streams")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "isaac_launcher",
                default_value="/home/peng/IsaacSim/_build/linux-x86_64/release/isaac-sim.sh",
            ),
            DeclareLaunchArgument(
                "scene_usd",
                default_value="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Environments/Office/office.usd",
            ),
            DeclareLaunchArgument(
                "robot_usd",
                default_value="/home/peng/isaacsim_assets/Assets/Isaac/5.1/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd",
            ),
            DeclareLaunchArgument("use_mock_streams", default_value="true"),
            LogInfo(msg=["[phase0] Isaac launcher candidate: ", isaac_launcher]),
            LogInfo(msg=["[phase0] Scene candidate: ", scene_usd]),
            LogInfo(msg=["[phase0] Robot candidate: ", robot_usd]),
            LogInfo(msg=["[phase0] Mock streams enabled: ", use_mock_streams]),
            LogInfo(
                msg=(
                    "[phase0] This bring-up entry stays lightweight on purpose. "
                    "Prompt 4 validates the release launcher, office.usd, Nova Carter, and the degraded replay bridge."
                )
            ),
        ]
    )
