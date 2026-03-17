from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


ROOT_DIR = "/home/peng/AgentSlam"
PYTHONPATH = f"{ROOT_DIR}/ros_ws/src/semantic_mapper_pkg:{ROOT_DIR}/ros_ws/src/sim_bridge_pkg"


def generate_launch_description() -> LaunchDescription:
    mode = LaunchConfiguration("mode")
    start_replay_publisher = LaunchConfiguration("start_replay_publisher")
    fixture_path = LaunchConfiguration("fixture_path")
    output_path = LaunchConfiguration("output_path")

    return LaunchDescription(
        [
            DeclareLaunchArgument("mode", default_value="bag_replay"),
            DeclareLaunchArgument("start_replay_publisher", default_value="true"),
            DeclareLaunchArgument(
                "fixture_path",
                default_value=f"{ROOT_DIR}/fixtures/semantic_mapping/office_nova_replay_scene.json",
            ),
            DeclareLaunchArgument(
                "output_path",
                default_value=f"{ROOT_DIR}/artifacts/phase1/office_nova_replay_semantic_map.launch.json",
            ),
            LogInfo(msg=["[phase1] mode: ", mode]),
            LogInfo(msg=["[phase1] replay fixture: ", fixture_path]),
            ExecuteProcess(
                condition=IfCondition(start_replay_publisher),
                cmd=[
                    "/usr/bin/python3",
                    "-m",
                    "sim_bridge_pkg.fixture_replay_publisher",
                    "--fixture",
                    fixture_path,
                    "--playback-rate",
                    "1.5",
                    "--source-mode",
                    "bag_replay",
                ],
                additional_env={"PYTHONPATH": PYTHONPATH},
                output="screen",
            ),
            ExecuteProcess(
                cmd=[
                    "/usr/bin/python3",
                    "-m",
                    "semantic_mapper_pkg.ros_node",
                    "--mode",
                    mode,
                    "--output",
                    output_path,
                    "--query-output-dir",
                    f"{ROOT_DIR}/artifacts/phase1/replay_queries",
                    "--query-label",
                    "chair",
                    "--query-label",
                    "desk",
                    "--query-label",
                    "cabinet",
                    "--expected-frames",
                    "3",
                    "--idle-timeout",
                    "4.0",
                ],
                additional_env={"PYTHONPATH": PYTHONPATH},
                output="screen",
            ),
        ]
    )
