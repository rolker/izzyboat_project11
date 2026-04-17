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

    return LaunchDescription([
        operator_namespace_arg,
        robot_namespace_arg,
        enable_bridge_arg,
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
                Node(
                    package='diagnostic_aggregator',
                    executable='aggregator_node',
                    name='diagnostic_aggregator',
                    parameters=[
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'config',
                            'diagnostics.yaml'
                        ])
                    ],
                    remappings=[
                        ('diagnostics', '/diagnostics'),
                        ('diagnostics_agg', '/diagnostics_agg'),
                        ('diagnostics_toplevel_state', '/diagnostics_toplevel_state'),
                    ],
                    output='screen',
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
