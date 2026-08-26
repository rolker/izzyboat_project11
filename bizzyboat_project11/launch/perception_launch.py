from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
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


# The recorder arguments this file used to declare, before the rosbag2
# recorders moved to logging_launch.py (#458).
MOVED_RECORDER_ARGUMENTS = (
    'log_directory',
    'log_subdirectory',
    'sonar_log_directory',
    'sonar_log_subdirectory',
)


def command_line_argument_names(context):
    """Return the `name:=value` names this launch was invoked with.

    `context.launch_configurations` is the wrong thing to test a stale
    argument against: it also holds whatever an *including* launch file
    declared, so a larger bring-up that legitimately has its own
    `log_directory` would trip a guard keyed on it and take the whole boat
    down. `ros2 launch` seeds `context.argv` with exactly the command-line
    `name:=value` pairs, which is the mistake these guards are for.
    """
    return {entry.split(':=', 1)[0]
            for entry in context.argv if ':=' in entry}


def reject_moved_recorder_arguments(context, *args, **kwargs):
    """Fail loudly on a `name:=value` this file no longer honours.

    `ros2 launch` does not validate top-level arguments: an undeclared
    `name:=value` just sets a launch configuration nobody reads. So a field
    script or a habit that still points the recorders at a chosen directory
    through *this* launch file would come up perfectly clean -- cameras, sonar
    and all -- while the bags went to the default location, and nothing would
    say so until someone went looking for the data. That is exactly the class
    of silent field failure this package tries not to ship, so it is a hard
    error naming where the argument went.

    Keyed on the command line only (see `command_line_argument_names`), so a
    bring-up that includes this file and declares one of these names for its
    own purposes is not what gets stopped.
    """
    supplied = command_line_argument_names(context)
    stale = [name for name in MOVED_RECORDER_ARGUMENTS if name in supplied]
    if stale:
        raise RuntimeError(
            'perception_launch.py no longer runs the rosbag2 recorders; '
            f"the argument(s) {', '.join(stale)} moved to logging_launch.py "
            '(#458) and would be ignored here, leaving the bags at their '
            'default location.\n\n'
            'Pass them to the logging launch instead, e.g.:\n'
            '  ros2 launch bizzyboat_project11 logging_launch.py '
            f'{stale[0]}:=<value>\n\n'
            "To relocate the M3's raw .all archive (which does still live "
            'here), use m3_all_directory:=<value> -- keep it off the sonar '
            'bag directory itself; a sibling of it is the default and the '
            'tidiest place for it.')
    return []


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    # Where the M3's raw Kongsberg .all archive writes when it is armed.
    # Its own argument, not the sonar bag's `sonar_log_directory` (which moved
    # to logging_launch.py with the recorders, #458): the two are independent
    # -- the bag is the boat's data of record, the .all is an opt-in debugging
    # artifact -- and sharing one argument across two launch files would let an
    # override applied to only one of them silently break the sibling-directory
    # invariant documented at the bridge below.
    m3_all_directory = LaunchConfiguration('m3_all_directory')
    m3_all_directory_arg = DeclareLaunchArgument(
        'm3_all_directory',
        default_value=PathJoinSubstitution([
            EnvironmentVariable(
                'P11_SONAR_LOG_DIR',
                default_value='/home/field/data/logs/bizzyboat_sonar'
            ),
            'm3_all'
        ]),
        description='Directory for the M3 raw Kongsberg .all archive. Only '
                    'written to once recording is armed via the bridge\'s '
                    'set_recording service (record_on_start defaults false).'
    )

    return LaunchDescription([
        # First, so a stale recorder argument stops the launch here rather
        # than part-way through a bring-up that would not have recorded.
        OpaqueFunction(function=reject_moved_recorder_arguments),
        namespace_arg,
        m3_all_directory_arg,

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
                                # Where the M3's raw Kongsberg EM stream is
                                # archived as genuine .all files
                                # (Caris/Qimera/MB-System) when recording is
                                # armed. This configures only *where*: the
                                # bridge's `record_on_start` defaults false
                                # (marine_tools#54), so the archive is opt-in
                                # and nothing is written until it is armed via
                                # the bridge's set_recording service.
                                #
                                # Default is an `m3_all` subdir of the
                                # sonar-log base, NOT the sonar bag's own
                                # `<base>/<sonar_log_subdirectory>` dir: the
                                # sonar_logger rosbag2 recorder errors if that
                                # exact dir pre-exists, and the bridge makedirs
                                # its save dir -- so aiming the archive at the
                                # bag dir itself would race the recorder.
                                # (The bag's *parent* is fine -- rosbag2 only
                                # objects to its own target -- but `m3_all` as
                                # a collision-free sibling also keeps the .all
                                # files out from among the bag directories.)
                                # Keep any override off the bag directory.
                                'save_all_dir': m3_all_directory,
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

                # The rosbag2 recorders used to live here; they moved to
                # logging_launch.py (#458) so recording can be stopped and
                # restarted without taking this chain down.
            ]
        ),
    ])
