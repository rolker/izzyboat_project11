from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    mikrotik_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'network_monitor_operator.yaml'
    ])

    teltonika_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'teltonika_monitor_operator.yaml'
    ])

    ping_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'ping_targets_operator.yaml'
    ])

    return LaunchDescription([
        Node(
            package='mikrotik_monitor',
            executable='mikrotik_monitor_node',
            name='mikrotik_monitor',
            parameters=[mikrotik_config],
            output='both',
        ),
        Node(
            package='teltonika_monitor',
            executable='teltonika_monitor_node',
            name='teltonika_monitor',
            parameters=[teltonika_config],
            output='both',
        ),
        Node(
            package='starlink_stats',
            executable='starlink_diagnostics_node',
            name='starlink_diagnostics',
            parameters=[{
                'dish_address': '192.168.100.1:9200',
                'poll_rate': 1.0,
                'hardware_id': 'starlink.op',
            }],
            output='both',
        ),
        Node(
            package='network_tools',
            executable='ping_monitor_node',
            name='ping_monitor',
            parameters=[ping_config],
            output='both',
        ),
    ])
