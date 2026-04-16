from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bizzyboat_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'bizzyboat.yaml'
    ])

    return LaunchDescription([
        Node(
            package='mikrotik_monitor',
            executable='mikrotik_monitor_node',
            name='mikrotik_monitor',
            parameters=[bizzyboat_config],
            output='screen',
        ),
        Node(
            package='teltonika_monitor',
            executable='teltonika_monitor_node',
            name='teltonika_monitor',
            parameters=[bizzyboat_config],
            output='screen',
        ),
        Node(
            package='starlink_stats',
            executable='starlink_diagnostics_node',
            name='starlink_diagnostics',
            parameters=[bizzyboat_config],
            output='screen',
        ),
        Node(
            package='network_tools',
            executable='ping_monitor_node',
            name='ping_monitor',
            parameters=[bizzyboat_config],
            output='screen',
        ),
    ])
