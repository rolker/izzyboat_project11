"""Operator-station core bringup for BizzyBoat.

Station-agnostic: the two things that differ between operator stations are
supplied here rather than baked into ``config/operator.yaml``.

``wifi`` (default true)
    Whether this station has a line-of-sight WiFi-bridge path to the boat.
    False for over-the-horizon operation — including the CCOM Telepresence
    Room, where the bridge radio is out of range — and layers
    ``config/operator_no_wifi.yaml``, which drops the ``wifi`` connection from
    udp_bridge's ``connections_list``.

``return_host_prefix`` (default: this machine's short hostname)
    Names the station to the boat. udp_bridge ships ``return_host`` to the
    remote, which then transmits there, so this must name *this* station or
    the downlink lands somewhere else. The three canonical forms come from
    ``dns_naming.md`` rule 8 in ccomjhc_project11 (operator hosts get one
    NETMAP address per boat, so configs use the vehicle-qualified form):

        wifi  ->  <prefix>.op.p11.lan
        vpn   ->  <prefix>.vpn.bizzy.p11.lan
        cell  ->  <prefix>.cell.bizzy.p11.lan

    Deriving these keeps one config valid for salmon, pandy and any future
    station: on salmon the derivation reproduces the literals this file used
    to carry. Override the argument if a station's hostname ever diverges
    from its DNS label.
"""

import socket

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.conditions import IfCondition
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from launch_ros.actions import SetParametersFromFile
from launch_ros.substitutions import FindPackageShare

# Boat-side remote name, and the vehicle qualifier in the NETMAP host names.
# Both are fixed by config/operator.yaml's remotes_list and by the BizzyBoat
# router's DNS zone, so they are not launch arguments.
REMOTE_NAME = 'bizzy'

# connection id -> DNS suffix appended to return_host_prefix.
RETURN_HOST_SUFFIXES = {
    'wifi': '.op.p11.lan',
    'vpn': f'.vpn.{REMOTE_NAME}.p11.lan',
    'cell': f'.cell.{REMOTE_NAME}.p11.lan',
}

def generate_launch_description():
    operator_namespace = LaunchConfiguration('operator_namespace')
    operator_namespace_arg = DeclareLaunchArgument(
        'operator_namespace', default_value=TextSubstitution(text='operator')
    )

    robot_namespace = LaunchConfiguration('robot_namespace')
    robot_namespace_arg = DeclareLaunchArgument(
        'robot_namespace', default_value=TextSubstitution(text='bizzy')
    )

    enable_bridge = LaunchConfiguration('enable_bridge')
    enable_bridge_arg = DeclareLaunchArgument(
        'enable_bridge', default_value='true'
    )

    # Plumbs through to bag_recorder_operator_launch.py. Default true so
    # deployment launches keep recording; pass record_diagnostics:=false
    # to bring up the operator core without the bag recorder (bench/test).
    record_diagnostics = LaunchConfiguration('record_diagnostics')
    record_diagnostics_arg = DeclareLaunchArgument(
        'record_diagnostics', default_value='true'
    )

    wifi = LaunchConfiguration('wifi')
    wifi_arg = DeclareLaunchArgument(
        'wifi', default_value='true',
        description='This station has a line-of-sight WiFi-bridge path to the '
                    'boat. Set false for over-the-horizon operation (e.g. the '
                    'ROC) to drop the wifi connection from udp_bridge.'
    )

    # Short hostname, lowercased and stripped of any domain part, so a host
    # configured as "pandy.p11.lan" still derives "pandy".
    station = socket.gethostname().split('.')[0].lower()
    return_host_prefix = LaunchConfiguration('return_host_prefix')
    return_host_prefix_arg = DeclareLaunchArgument(
        'return_host_prefix', default_value=station,
        description='Station name the boat transmits back to; the DNS suffix '
                    'for each path is appended to it. Defaults to this '
                    "machine's short hostname."
    )

    # udp_bridge only re-points an existing boat-side connection when
    # return_host is non-empty, so these are always set, for every connection
    # in the file. An override for a connection dropped by wifi:=false is
    # simply never read.
    return_host_params = [
        SetParameter(
            name=f'remotes.{REMOTE_NAME}.connections.{connection}.return_host',
            value=[return_host_prefix, TextSubstitution(text=suffix)]
        )
        for connection, suffix in RETURN_HOST_SUFFIXES.items()
    ]

    # Announced at startup because a wrong return host is otherwise invisible
    # from this end: the bridge comes up clean and the downlink goes elsewhere.
    return_host_announcement = LogInfo(
        msg=['operator station return hosts: ',
             return_host_prefix, TextSubstitution(text=RETURN_HOST_SUFFIXES['vpn']),
             ' (vpn), ',
             return_host_prefix, TextSubstitution(text=RETURN_HOST_SUFFIXES['cell']),
             ' (cell)']
    )

    return LaunchDescription([
        operator_namespace_arg,
        robot_namespace_arg,
        enable_bridge_arg,
        record_diagnostics_arg,
        wifi_arg,
        return_host_prefix_arg,
        return_host_announcement,
        GroupAction(
            actions=[
                PushRosNamespace(operator_namespace),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'operator.yaml'
                    ])
                ),
                # Delta, not a copy: shortens connections_list only. Must load
                # after the base file so its shorter list wins.
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'operator_no_wifi.yaml'
                    ]),
                    condition=UnlessCondition(wifi)
                ),
                *return_host_params,
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('udp_bridge'),
                            'launch',
                            'udp_bridge_launch.py'
                        ])
                    ),
                    condition=IfCondition(enable_bridge)
                ),
            ]
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'network_monitor_operator_launch.py'
                ])
            ),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'bag_recorder_operator_launch.py'
                ])
            ),
            launch_arguments={
                'record_diagnostics': record_diagnostics,
            }.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('marine_autonomy'),
                    'launch',
                    'operator_core_launch.py'
                ])
            ),
            launch_arguments={
                'operator_namespace': operator_namespace,
                'robot_namespace': robot_namespace,
                'enable_bridge': 'false',
                'operator_joystick': 'true'
            }.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'publish_state_launch.py'
                ])
            ),
            launch_arguments={
                'namespace': robot_namespace,
            }.items()
        ),
    ])
