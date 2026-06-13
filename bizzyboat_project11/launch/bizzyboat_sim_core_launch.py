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
    """Sim-aware BizzyBoat core bringup (non-Gazebo Massabesic sim).

    Brings up only the sim-shareable autonomy stack — transforms, the
    marine_autonomy robot core, and nav2 — reusing the boat's REAL config
    files. Hardware drivers wired by ``core_launch.py`` (mavros/FCU, SBG INS,
    NTRIP, Garmin sidescan, sound-speed and ZDA serial bridges, network
    monitor, GPS-RTK diagnostics, mavros frame bridges) are intentionally
    excluded: in sim, ``asv_sim`` is the vehicle and ``mbes_sim`` the sonar.

    Mirrors ``ben_project11/ben_core_launch.py``'s base-config +
    ``*_sim.yaml``-overlay pattern so sim and field share one config source
    (no duplication / drift): ``bizzyboat.yaml`` always, then
    ``bizzyboat_sim.yaml`` only under ``is_simulator``. nav2 is included via
    the real ``nav_launch.py`` (model 240 + ``nav2_overlay.yaml``) — not
    re-specified here. The helm (``asv_helm``) and ``asv_sim`` are supplied by
    the sim repo's ``sim_robot_launch.py``, as for Ben; ``echo_helm`` (the
    hardware helm) is therefore omitted.
    """
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    frame_prefix = LaunchConfiguration('frame_prefix')
    frame_prefix_arg = DeclareLaunchArgument(
        'frame_prefix', default_value='bizzy/'
    )

    # Exposed for parity with ben_core_launch.py; this launch is sim-only, so
    # the overlay is applied by default.
    is_simulator = LaunchConfiguration('is_simulator')
    is_simulator_arg = DeclareLaunchArgument(
        'is_simulator', default_value=TextSubstitution(text='true'),
        description='Layer bizzyboat_sim.yaml (sim nav sourcing + sim tide '
        'threshold) on top of bizzyboat.yaml.'
    )

    use_ca_safety = LaunchConfiguration('use_ca_safety')
    use_ca_safety_arg = DeclareLaunchArgument(
        'use_ca_safety', default_value='true',
        description='Pass-through to nav_launch.py: CA safety helm gate '
        '(default) vs the nav2 Collision Monitor.'
    )

    return LaunchDescription([
        namespace_arg,
        frame_prefix_arg,
        is_simulator_arg,
        use_ca_safety_arg,

        # URDF / robot_state_publisher (outside the namespace group —
        # publish_state_launch.py sets the namespace on its nodes itself).
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'publish_state_launch.py'
                ])
            ),
            launch_arguments={'namespace': namespace}.items()
        ),

        GroupAction(
            actions=[
                PushRosNamespace(namespace),

                # Base config (real, always), then sim deltas only.
                # bizzyboat_sim.yaml never duplicates planner/costmap config —
                # that lives in nav2_overlay.yaml, loaded by nav_launch.py.
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'bizzyboat.yaml'
                    ])
                ),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'bizzyboat_sim.yaml'
                    ]),
                    condition=IfCondition(is_simulator)
                ),

                # MRU transform (map/odom/base_link TF). In sim it sources nav
                # from asv_sim via the bizzyboat_sim.yaml overlay (the base
                # config points it at mavros, which does not run in sim).
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

                # Sea surface estimator: publishes map -> map_tide TF.
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
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('mru_transform'),
                            'launch',
                            'chart_datum_launch.py'
                        ])
                    ),
                ),

                # Marine autonomy robot core (mission manager, helm manager,
                # status — the autonomy side of the helm; the actuating helm
                # is asv_helm from the sim repo).
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

                # S57 charts (mirrors the field bringup; harmless where no ENC
                # coverage exists, e.g. Lake Massabesic).
                GroupAction(
                    actions=[
                        PushRosNamespace('s57'),
                        SetParameter(
                            name='map_frame',
                            value=[frame_prefix, 'map']
                        ),
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
            ]
        ),

        # Nav2 — reuse the real bizzy nav_launch.py (model 240 +
        # nav2_overlay.yaml + costmap window). No nav2 config duplication:
        # this is the same launch the boat runs in the field.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'launch',
                    'nav_launch.py'
                ])
            ),
            launch_arguments={
                'namespace': namespace,
                'use_ca_safety': use_ca_safety,
            }.items()
        ),
    ])
