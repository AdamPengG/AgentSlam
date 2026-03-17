from launch import LaunchDescription
from launch.actions import ExecuteProcess


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            ExecuteProcess(
                cmd=[
                    "bash",
                    "/home/peng/AgentSlam/scripts/run_phase1_fixture.sh",
                ],
                output="screen",
            )
        ]
    )
