from launch import LaunchDescription
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def _oak_camera_group(name):
    return GroupAction(
        actions=[
            PushRosNamespace(name),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        FindPackageShare('depthai_ros_driver'),
                        'launch',
                        'camera.launch.py'
                    ])
                ),
                launch_arguments={
                    'params_file': PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        name + '.yaml'
                    ]),
                    'name': name,
                }.items()
            ),
        ]
    )


def generate_launch_description():
    return LaunchDescription([
        _oak_camera_group('oak_forward'),
        _oak_camera_group('oak_starboard'),
        _oak_camera_group('oak_aft'),
        _oak_camera_group('oak_port'),
    ])
