from launch import LaunchDescription
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    return LaunchDescription([
        GroupAction(
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('izzyboat_project11'),
                            'launch',
                            'operator_core_launch.py'
                        ])
                    ),
                )
            ]
        ),
        GroupAction(
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('izzyboat_project11'),
                            'launch',
                            'operator_ui_launch.py'
                        ])
                    ),
                ),
            ]
        ),
        GroupAction(
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('molab_hardware'),
                            'launch',
                            'mobile_lab_launch.py'
                        ])
                    )
                ),
            ]
        )
    ])


