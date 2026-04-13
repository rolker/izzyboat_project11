from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_file = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'network_monitor_operator.yaml'
    ])

    return LaunchDescription([
        Node(
            package='mikrotik_monitor',
            executable='mikrotik_monitor_node',
            name='mikrotik_monitor',
            parameters=[config_file],
            output='screen',
        ),
    ])
