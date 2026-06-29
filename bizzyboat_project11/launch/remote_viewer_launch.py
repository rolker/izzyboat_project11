"""Lightweight remote-viewer station for monitoring BizzyBoat (#354).

Brings up a udp_bridge endpoint named ``remote`` plus CAMP, under the ``remote``
namespace, on a non-operator machine. Unlike the operator station, no static
remotes/connections/topic list is configured here — the link to the boat is set
up live through the udp_bridge rqt plugin. Intended for passive situational
awareness (e.g. watching the boat come into the dock).

    ros2 launch bizzyboat_project11 remote_viewer_launch.py
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParametersFromFile
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='remote')
    )

    robot_namespace = LaunchConfiguration('robot_namespace')
    robot_namespace_arg = DeclareLaunchArgument(
        'robot_namespace', default_value=TextSubstitution(text='bizzy')
    )

    enable_bridge = LaunchConfiguration('enable_bridge')
    enable_bridge_arg = DeclareLaunchArgument(
        'enable_bridge', default_value='true'
    )

    camp = LaunchConfiguration('camp')
    camp_arg = DeclareLaunchArgument(
        'camp', default_value='true'
    )

    background_chart = LaunchConfiguration('background_chart')
    background_chart_arg = DeclareLaunchArgument(
        'background_chart',
        default_value=PathJoinSubstitution([
            FindPackageShare('camp'), 'workspace', '13283', '13283_2.KAP'
        ])
    )

    # udp_bridge endpoint (name: remote) under the remote namespace. The /**/
    # wildcard in remote.yaml matches the node regardless of the pushed namespace.
    bridge_group = GroupAction(
        actions=[
            PushRosNamespace(namespace),
            SetParametersFromFile(
                filename=PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'config',
                    'remote.yaml'
                ])
            ),
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
    )

    # CAMP, mirroring the operator_ui pattern: arguments are the workspace dir
    # and the background chart; robot_namespace points the display at the boat.
    camp_node = Node(
        package='camp',
        executable='CCOMAutonomousMissionPlanner',
        name='camp',
        namespace=namespace,
        arguments=[
            PathJoinSubstitution([FindPackageShare('camp'), 'workspace/']),
            background_chart
        ],
        parameters=[{'robot_namespace': robot_namespace}],
        condition=IfCondition(camp),
        respawn=True,
        respawn_delay=5,
        emulate_tty=True
    )

    return LaunchDescription([
        namespace_arg,
        robot_namespace_arg,
        enable_bridge_arg,
        camp_arg,
        background_chart_arg,
        bridge_group,
        camp_node,
    ])
