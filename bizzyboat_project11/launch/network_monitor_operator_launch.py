"""Operator-station network monitoring.

Which of these nodes can succeed depends on what the station physically has,
so two launch arguments gate them rather than every station carrying a config
variant. They are deliberately independent: whether a station has a WiFi
bridge radio and whether it has a Starlink dish are separate facts. The ROC
happens to have neither, but conflating them would bake a site name into an
argument that is really about equipment.

``wifi`` (default true)
    Station has a line-of-sight WiFi-bridge path to the boat. False drops the
    mikrotik monitor (there is no operator-side bridge radio to poll) and
    selects the ping-target list without the direct/WiFi-path targets.

``op_starlink`` (default true)
    Station has its own Starlink dish. False drops the Starlink diagnostics
    node; without a dish it can only ever report an error, and a permanently
    red row is how operators learn to stop reading the annunciator.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.conditions import UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    wifi = LaunchConfiguration('wifi')
    wifi_arg = DeclareLaunchArgument(
        'wifi', default_value='true',
        description='Station has a WiFi-bridge path to the boat. False drops '
                    'the mikrotik monitor and the direct-path ping targets.'
    )

    op_starlink = LaunchConfiguration('op_starlink')
    op_starlink_arg = DeclareLaunchArgument(
        'op_starlink', default_value='true',
        description='Station has its own Starlink dish. False drops the '
                    'Starlink diagnostics node.'
    )

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

    # Two complete lists rather than a base plus a delta: ping_monitor takes
    # `targets` as a flat string array, so a second file replaces the list
    # instead of shortening it. Kept in step by test_operator_core_launch.py.
    ping_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'ping_targets_operator.yaml'
    ])

    ping_config_no_wifi = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'ping_targets_operator_no_wifi.yaml'
    ])

    return LaunchDescription([
        wifi_arg,
        op_starlink_arg,
        # Polls the operator-side bridge radio (bizzy.wifi.op). Skipped rather
        # than pointed elsewhere when the station has no radio: the host is
        # absent, not temporarily unreachable, and a node that cannot succeed
        # should not run.
        Node(
            package='mikrotik_monitor',
            executable='mikrotik_monitor_node',
            name='mikrotik_monitor',
            parameters=[mikrotik_config],
            output='both',
            condition=IfCondition(wifi),
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
            condition=IfCondition(op_starlink),
        ),
        Node(
            package='network_tools',
            executable='ping_monitor_node',
            name='ping_monitor',
            parameters=[ping_config],
            output='both',
            condition=IfCondition(wifi),
        ),
        Node(
            package='network_tools',
            executable='ping_monitor_node',
            name='ping_monitor',
            parameters=[ping_config_no_wifi],
            output='both',
            condition=UnlessCondition(wifi),
        ),
    ])
