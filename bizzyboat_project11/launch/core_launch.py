from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from launch_ros.actions import SetParametersFromFile
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

    fcu_url = LaunchConfiguration('fcu_url')
    fcu_url_arg = DeclareLaunchArgument(
        'fcu_url', default_value=TextSubstitution(text='/dev/fcu:57600')
    )

    gcs_url = LaunchConfiguration('gcs_url')
    gcs_url_arg = DeclareLaunchArgument(
        'gcs_url', default_value=TextSubstitution(text='')
    )

    return LaunchDescription([
        namespace_arg,
        frame_prefix_arg,
        fcu_url_arg,
        gcs_url_arg,

        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'bizzyboat.yaml'
                    ])
                ),

                # MRU transform
                Node(
                    package='mru_transform',
                    executable='mru_transform_node',
                    name='mru_transform',
                    parameters=[{
                        'map_frame': [frame_prefix, 'map'],
                        'base_frame': [frame_prefix, 'base_link'],
                        'odom_frame': [frame_prefix, 'odom'],
                    }],
                    emulate_tty=True
                ),

                # Sea surface estimator
                SetParameter(
                    name='sea_surface_frame',
                    value=[frame_prefix, 'map_tide']
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('mru_transform'),
                            'launch',
                            'sea_surface_estimator_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'namespace': namespace,
                        'enable_bridge': 'false',
                    }.items()
                ),

                # MAVRos
                GroupAction(
                    actions=[
                        PushRosNamespace('mavros'),
                        Node(
                            package='mavros',
                            executable='mavros_node',
                            parameters=[
                                {
                                    'fcu_url': fcu_url,
                                    'gcs_url': gcs_url,
                                    'target_system': 1,
                                    'target_component': 1,
                                    'fcu_protocol': 'v2.0'
                                },
                                PathJoinSubstitution([
                                    FindPackageShare('mavros'),
                                    'launch',
                                    'apm_pluginlists.yaml'
                                ]),
                                PathJoinSubstitution([
                                    FindPackageShare('mavros'),
                                    'launch',
                                    'apm_config.yaml'
                                ]),
                                PathJoinSubstitution([
                                    FindPackageShare('echoboat_project11'),
                                    'config',
                                    'mavros.yaml'
                                ]),
                            ],
                            respawn=True,
                            respawn_delay=5.0,
                            emulate_tty=True
                        ),
                    ]
                ),

                # UDP bridge
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('udp_bridge'),
                            'launch',
                            'udp_bridge_launch.py'
                        ])
                    )
                ),

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

        # URDF / robot state publisher (outside namespace group —
        # publish_state_launch.py sets namespace on nodes directly)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'publish_state_launch.py'
                ])
            ),
            launch_arguments={
                'namespace': namespace
            }.items()
        ),

        # NTRIP — disabled until credentials are configured
        # IncludeLaunchDescription(
        #     PythonLaunchDescriptionSource(
        #         PathJoinSubstitution([
        #             FindPackageShare('bizzyboat_project11'),
        #             'launch',
        #             'ntrip_launch.py'
        #         ])
        #     ),
        # ),
    ])
