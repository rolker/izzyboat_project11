from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mikrotik_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'network_monitor_boat.yaml'
    ])

    teltonika_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'teltonika_monitor_boat.yaml'
    ])

    return LaunchDescription([
        Node(
            package='mikrotik_monitor',
            executable='mikrotik_monitor_node',
            name='mikrotik_monitor',
            parameters=[mikrotik_config],
            output='screen',
        ),
        Node(
            package='teltonika_monitor',
            executable='teltonika_monitor_node',
            name='teltonika_monitor',
            parameters=[teltonika_config],
            output='screen',
        ),
        Node(
            package='starlink_stats',
            executable='starlink_diagnostics_node',
            name='starlink_diagnostics',
            parameters=[{
                'dish_address': '192.168.100.1:9200',
                'poll_rate': 1.0,
            }],
            output='screen',
        ),
    ])
