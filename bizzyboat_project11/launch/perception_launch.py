import datetime

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParametersFromFile
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    log_directory = LaunchConfiguration('log_directory')
    log_directory_arg = DeclareLaunchArgument(
        'log_directory',
        default_value=EnvironmentVariable(
            'P11_LOG_DIR',
            default_value='/home/field/data/logs/bizzyboat'
        )
    )

    sonar_log_directory = LaunchConfiguration('sonar_log_directory')
    sonar_log_directory_arg = DeclareLaunchArgument(
        'sonar_log_directory',
        default_value=EnvironmentVariable(
            'P11_SONAR_LOG_DIR',
            default_value='/home/field/data/logs/bizzyboat_sonar'
        )
    )
    datetime_str = datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec='seconds').replace(':', '-')
    log_subdirectory = LaunchConfiguration('log_subdirectory')
    log_subdirectory_arg = DeclareLaunchArgument(
        'log_subdirectory',
        default_value=TextSubstitution(text=datetime_str)
    )
    sonar_log_subdirectory = LaunchConfiguration('sonar_log_subdirectory')
    sonar_log_subdirectory_arg = DeclareLaunchArgument(
        'sonar_log_subdirectory',
        default_value=TextSubstitution(text=datetime_str)
    )

    return LaunchDescription([
        namespace_arg,
        log_directory_arg,
        log_subdirectory_arg,
        sonar_log_directory_arg,
        sonar_log_subdirectory_arg,

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

                # DeltaT sonar + cube bathymetry
                GroupAction(
                    actions=[
                        PushRosNamespace('sensors/deltat'),
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('imagenex_deltat'),
                                    'launch',
                                    'deltat_launch.py'
                                ])
                            )
                        ),
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('cube_bathymetry'),
                                    'launch',
                                    'cube_bathymetry_launch.py'
                                ])
                            )
                        ),
                    ]
                ),

                # M3 multibeam + cube bathymetry.
                # Unlike the DeltaT (which publishes `soundings` directly), the
                # M3 chain is three nodes: kongsberg_em_bridge decodes the M3's
                # UDP Kongsberg .all stream to SonarDetections, then
                # detections_to_pointcloud -> cube_bathymetry_node grid it. The
                # bridge stamps `bizzy/m3` (the URDF transducer frame, #221).
                GroupAction(
                    actions=[
                        PushRosNamespace('sensors/m3'),
                        Node(
                            package='kongsberg_em_bridge',
                            executable='kongsberg_em_bridge',
                            name='kongsberg_em_bridge',
                            parameters=[{
                                'bind_port': 20002,
                                'frame_id': 'bizzy/m3',
                                # Archive the M3's raw Kongsberg EM stream as
                                # genuine .all files (Caris/Qimera/MB-System)
                                # alongside the sonar bags. Use an `m3_all`
                                # subdir of the sonar-log base, NOT the bag's
                                # own `<base>/<sonar_log_subdirectory>` dir:
                                # the sonar_logger rosbag2 recorder errors if
                                # its target dir pre-exists, and the bridge
                                # makedirs its save dir -- so writing there (or
                                # to that session parent) would race the bag.
                                # `<base>/m3_all` is a collision-free sibling.
                                'save_all_dir': PathJoinSubstitution([
                                    sonar_log_directory, 'm3_all'
                                ]),
                                # Prototype rollover: cap each .all segment at
                                # 200 MB (about every ~12 min at the M3's
                                # current rate) so files stay manageable. Set
                                # save_all_max_seconds instead/also for
                                # time-based splits; 0 = trigger off. NOTE:
                                # split segments do not yet re-emit the
                                # installation/SVP (I/73) datagrams at their
                                # head, so a mid-stream file may not load
                                # cleanly in Caris/Qimera (deferred).
                                'save_all_max_bytes': 200000000,
                                'save_all_max_seconds': 0.0,
                            }],
                            emulate_tty=True,
                            # Auto-restart like the boat's other UDP/serial
                            # drivers (cameras, SBG, sidescan, ntrip,
                            # sound_speed) so a transient bridge crash does not
                            # silently kill M3 bathymetry. Respawn opens a fresh
                            # .all segment (timestamped, never overwrites).
                            respawn=True,
                            respawn_delay=5.0,
                        ),
                        # detections_to_pointcloud reads "odom" for speed-over-
                        # ground; it lives outside this sensors/m3 namespace.
                        # (Its TF frame params are set in bizzyboat.yaml.)
                        SetRemap(src='odom', dst='/bizzy/odom'),
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('cube_bathymetry'),
                                    'launch',
                                    'detections_to_pointcloud_launch.py'
                                ])
                            )
                        ),
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('cube_bathymetry'),
                                    'launch',
                                    'cube_bathymetry_launch.py'
                                ])
                            )
                        ),
                    ]
                ),

                # Cameras
                GroupAction(
                    actions=[
                        PushRosNamespace('sensors/cameras'),

                        # USB camera (definition shared with the cameras-only
                        # test launch; edit usb_camera_launch.py, not here)
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('bizzyboat_project11'),
                                    'launch',
                                    'usb_camera_launch.py'
                                ])
                            ),
                        ),

                        # 4x OAK cameras
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('bizzyboat_project11'),
                                    'launch',
                                    'oak_cameras_launch.py'
                                ])
                            ),
                        ),

                        # Reflex collision-avoidance pointcloud (#170): forward-OAK
                        # segmentation projected to base_link_level for the nav2
                        # Collision Monitor (perception#17 segments_to_pointcloud,
                        # reflex mode). Under oak_forward/ so its relative
                        # `segmentation` + `segmentation/camera_info` subscriptions
                        # resolve to the forward camera; `~/pointcloud` is remapped
                        # to the canonical /<ns>/collision_monitor/pointcloud topic
                        # consumed by the bag/bridge configs and the Collision
                        # Monitor (Phase B).
                        GroupAction(
                            actions=[
                                PushRosNamespace('oak_forward'),
                                SetRemap(
                                    src='~/pointcloud',
                                    dst=['/', namespace,
                                         '/collision_monitor/pointcloud']
                                ),
                                IncludeLaunchDescription(
                                    PythonLaunchDescriptionSource(
                                        PathJoinSubstitution([
                                            FindPackageShare(
                                                'sea_surface_segmentation'),
                                            'launch',
                                            'segments_to_pointcloud_launch.py'
                                        ])
                                    ),
                                    launch_arguments={
                                        'name': 'segments_to_pointcloud_reflex',
                                        'target_frame': 'bizzy/base_link_level',
                                        # Reflex confidence floor: drop low-
                                        # confidence returns (calm-water
                                        # reflections ~0.55) so the e-stop reacts
                                        # to real obstacles (buoys/pots 0.85+).
                                        # "Balanced" default; raise to ~0.75 on
                                        # glassy water via ros2 param set. See
                                        # unh_marine_perception#35/#37/#34.
                                        'obstacle_prob_min': '0.60',
                                    }.items()
                                ),
                            ]
                        ),
                    ]
                ),

                # Rosbag logger
                Node(
                    package='rosbag2_transport',
                    executable='recorder',
                    name='logger',
                    parameters=[
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'config',
                            'bizzyboat.yaml'
                        ]),
                        {'storage.uri': PathJoinSubstitution([
                            log_directory,
                            log_subdirectory
                        ])}
                    ],
                    emulate_tty=True
                ),

                # Sonar logger
                Node(
                    package='rosbag2_transport',
                    executable='recorder',
                    name='sonar_logger',
                    parameters=[
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'config',
                            'bizzyboat.yaml'
                        ]),
                        {'storage.uri': PathJoinSubstitution([
                            sonar_log_directory,
                            sonar_log_subdirectory
                        ])},
                    ],
                    emulate_tty=True
                ),
            ]
        ),
    ])
