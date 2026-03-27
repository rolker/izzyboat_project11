from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    frame_prefix = LaunchConfiguration('frame_prefix')
    frame_prefix_arg = DeclareLaunchArgument(
        'frame_prefix', default_value='bizzy/'
    )

    return LaunchDescription([
        namespace_arg,
        frame_prefix_arg,

        GroupAction(
            actions=[
                PushRosNamespace(namespace),

                # Marine autonomy robot core
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('marine_autonomy'),
                            'launch',
                            'robot_core_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'namespace': namespace,
                        'enable_bridge': 'false',
                    }.items()
                ),

                # Echo helm
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('echo_helm'),
                            'launch',
                            'echo_helm_launch.py'
                        ])
                    ),
                ),

                # S57 charts
                GroupAction(
                    actions=[
                        PushRosNamespace('s57'),
                        SetParameter(
                            name='map_frame',
                            value=[frame_prefix, 'map']
                        ),
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('s57_grids'),
                                    'launch',
                                    's57_grids_launch.py'
                                ])
                            ),
                        )
                    ]
                ),
            ]
        ),

        # Nav2
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('echoboat_project11'),
                    'launch',
                    'nav2_bringup_launch.py'
                ])
            ),
            launch_arguments={
                'namespace': namespace,
                'use_namespace': 'true',
                'use_composition': 'False',
            }.items()
        ),
    ])
