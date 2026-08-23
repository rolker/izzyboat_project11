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

    # Garmin GCV-20 sidescan. On by default so it comes up with the boat; the
    # driver transmits nothing until commanded and is gated on a valid sound
    # speed, so with the mercat proxy or GCV absent it simply retries (no harm).
    # Disable with sidescan:=false.
    sidescan = LaunchConfiguration('sidescan')
    sidescan_arg = DeclareLaunchArgument(
        'sidescan', default_value='true'
    )

    # AIS decode chain (shore receiver over UDP). On by default; the chain is
    # passive and degrades to publishing nothing if the feed is absent.
    # Disable with ais:=false.
    ais = LaunchConfiguration('ais')
    ais_arg = DeclareLaunchArgument(
        'ais', default_value='true',
        description='Start the AIS decode chain (shore receiver on UDP 2125). '
                    'Set false to run without AIS; ais_layer then ages out its '
                    'contacts and contributes nothing to the costmap.'
    )

    return LaunchDescription([
        namespace_arg,
        frame_prefix_arg,
        fcu_url_arg,
        gcs_url_arg,
        sidescan_arg,
        ais_arg,

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

                # Chart datum (MLLW vertical datum transform).
                # Lake Massabesic datum comes from the polygon config
                # (override:true entry, chart_datum_z = 48.88 m full-pool); no
                # scalar lake_datum param is set, so the polygon is the live
                # source (single source of truth, toward unh_marine_autonomy#163).
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('mru_transform'),
                            'launch',
                            'chart_datum_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'datum_config_path': PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'config',
                            'massabesic_datum_polygons.yaml'
                        ])
                    }.items(),
                ),

                # MAVROS frame bridges (workaround)
                #
                # mavros's local_position plugin lacks a `child_frame_id`
                # parameter (only global_position has one), so its messages
                # and static TFs use bare names — `map`, `odom`, `base_link`
                # — disconnected from the bizzy/ URDF tree. Identity transforms
                # here connect the bare frames under bizzy/ so TF lookups
                # (e.g. mru_transform's velocity body) resolve.
                Node(
                    package='tf2_ros',
                    executable='static_transform_publisher',
                    name='mavros_frame_bridge_map',
                    arguments=[
                        '--x', '0', '--y', '0', '--z', '0',
                        '--roll', '0', '--pitch', '0', '--yaw', '0',
                        '--frame-id', [frame_prefix, 'map'],
                        '--child-frame-id', 'map',
                    ],
                ),
                Node(
                    package='tf2_ros',
                    executable='static_transform_publisher',
                    name='mavros_frame_bridge_odom',
                    arguments=[
                        '--x', '0', '--y', '0', '--z', '0',
                        '--roll', '0', '--pitch', '0', '--yaw', '0',
                        '--frame-id', [frame_prefix, 'odom'],
                        '--child-frame-id', 'odom',
                    ],
                ),
                Node(
                    package='tf2_ros',
                    executable='static_transform_publisher',
                    name='mavros_frame_bridge_base_link',
                    arguments=[
                        '--x', '0', '--y', '0', '--z', '0',
                        '--roll', '0', '--pitch', '0', '--yaw', '0',
                        '--frame-id', [frame_prefix, 'base_link'],
                        '--child-frame-id', 'base_link',
                    ],
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
                                # Bizzyboat-specific mavros overrides: frame_ids
                                # on plugin sub-nodes. Must be a yaml (not an
                                # inline dict), because each plugin runs as its
                                # own node (e.g. /bizzy/mavros/imu) and only the
                                # /**/plugin_name: pattern reaches them — an
                                # inline dict binds to the main mavros_node.
                                PathJoinSubstitution([
                                    FindPackageShare('bizzyboat_project11'),
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

                # Ellipsoidal-height correction for the mavros fused fix.
                # mru_transform reads the output of this node, not
                # mavros/global_position/global -- see the fcu block in
                # bizzyboat.yaml for why.
                Node(
                    package='echo_helm',
                    executable='ellipsoidal_fix_node',
                    name='ellipsoidal_fix',
                    parameters=[{
                        'input_topic': 'mavros/global_position/global',
                        'raw_fix_topic': 'mavros/global_position/raw/fix',
                        'gps_raw_topic': 'mavros/gpsstatus/gps1/raw',
                        'output_topic': 'mavros/global_position/global_ellipsoidal',
                        'diagnostic_name': 'GPS: ellipsoidal fix',
                    }],
                    # This node now owns the FCU navigation position that reaches
                    # mru_transform, so a crash that left it down would be an
                    # open-ended vertical outage. Matches mavros beside it.
                    respawn=True,
                    respawn_delay=2,
                    emulate_tty=True
                ),

                # GPS RTK diagnostics
                Node(
                    package='bizzyboat_project11',
                    executable='gps_rtk_diagnostics_node.py',
                    name='gps_rtk_diagnostics',
                    parameters=[{
                        'gps_raw_topic': 'mavros/gpsstatus/gps1/raw',
                        'diagnostic_name': 'GPS: RTK',
                        'ok_min_fix_type': 6,
                        'warn_min_fix_type': 3,
                    }],
                    # Same argument as ellipsoidal_fix above and mavros before
                    # it: a diagnostics node that stays down publishes nothing,
                    # and nothing renders on the annunciator as a missing tile
                    # rather than a fault.
                    respawn=True,
                    respawn_delay=2,
                    emulate_tty=True
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
                #
                # enable_ellipsoidal_fix:=false because BizzyBoat launches its
                # own copy of ellipsoidal_fix_node above, carrying this hull's
                # topic parameters. echo_helm_launch.py gained the same node
                # (seafloor_echoboat_project11#56) so every EchoBoat gets the
                # correction -- the defect is a property of mavros behind an
                # ArduPilot FCU, not of one hull -- but two copies in the
                # bizzy namespace would publish duplicates on the output topic.
                # Drop the node above and remove this argument once the shared
                # launch can take the topic names as launch arguments.
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('echo_helm'),
                            'launch',
                            'echo_helm_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'enable_ellipsoidal_fix': 'false',
                    }.items(),
                ),

                # S57 charts
                GroupAction(
                    actions=[
                        PushRosNamespace('s57'),
                        SetParameter(
                            name='map_frame',
                            value=[frame_prefix, 'map']
                        ),
                        # Eager chart precompute: when TF (map → robot_base_frame)
                        # first becomes available, queue all charts within
                        # precompute_radius for std::async processing so the
                        # costmap layer's first get_datasets call finds them
                        # already cached or close to ready. Cuts cold-cache
                        # startup latency. Requires rolker/s57_tools#19.
                        SetParameter(
                            name='robot_base_frame',
                            value=[frame_prefix, 'base_link']
                        ),
                        SetParameter(
                            name='precompute_radius',
                            value=5000.0
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

                # AIS (shore receiver -> UDP 2125 -> contacts for ais_layer).
                # On by default so it comes up with the boat. The chain is
                # passive: with no feed reaching the boat the relay simply
                # blocks on an empty socket, no contacts are published, and
                # ais_layer ages out whatever it had and contributes nothing —
                # so a dead link degrades to "no AIS", never to an obstruction.
                # Disable with ais:=false.
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'launch',
                            'ais_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'namespace': namespace,
                    }.items(),
                    condition=IfCondition(ais)
                ),

                # Network monitor (boat side)
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'launch',
                            'network_monitor_boat_launch.py'
                        ])
                    ),
                ),

                # Sound-speed bridge (AML SVS on gabby /dev/ttyS0
                # -> ROS topic + Valeport UDP to M3 on mercat:20003;
                # ttyS1 belongs to the SBG — see sound_speed_launch.py)
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'launch',
                            'sound_speed_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'frame_prefix': frame_prefix,
                    }.items()
                ),

                # Garmin GCV-20 sidescan (gabby driver -> mercat proxy -> GCV).
                # On by default; disable with sidescan:=false.
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'launch',
                            'sidescan_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'namespace': namespace,
                        'frame_prefix': frame_prefix,
                    }.items(),
                    condition=IfCondition(sidescan)
                ),

                # ZDA serial bridge (SBG SbgUtcTime -> $GPZDA on
                # gabby /dev/ttyS2 -> M3 sonar serial input)
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'launch',
                            'zda_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'namespace': namespace,
                    }.items()
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

        # NTRIP
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'ntrip_launch.py'
                ])
            ),
            launch_arguments={
                'namespace': namespace,
            }.items()
        ),

        # SBG Ellipse-D INS (gabby's PORT_E). Logs nav data for FCU
        # parity comparison and forwards NTRIP RTCM to the SBG.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'sbg_launch.py'
                ])
            ),
            launch_arguments={
                'namespace': namespace,
            }.items()
        ),
    ])
