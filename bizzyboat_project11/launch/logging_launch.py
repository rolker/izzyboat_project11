import datetime

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import EnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.substitutions import FindPackageShare


# Arguments that live in perception_launch.py, not here (#458). The relocation
# table in the operator manual lists all three data destinations together, so
# reaching for the wrong launch file is the natural mistake -- and
# `ros2 launch` would accept it silently.
PERCEPTION_ARGUMENTS = (
    'm3_all_directory',
)


def reject_perception_arguments(context, *args, **kwargs):
    """Fail loudly on a `name:=value` that belongs to perception_launch.py.

    The mirror image of that file's `reject_moved_recorder_arguments`: an
    undeclared top-level argument just sets a launch configuration nobody
    reads, so `m3_all_directory:=/mnt/disk` passed here would start the
    recorders looking perfectly normal while the M3's raw `.all` archive kept
    filling the internal disk -- discovered, at the earliest, when someone went
    looking for the files.

    Nothing includes this launch file, so an inherited configuration cannot
    trip this by accident; if that ever changes, scope the include.
    """
    stale = [name for name in PERCEPTION_ARGUMENTS
             if name in context.launch_configurations]
    if stale:
        raise RuntimeError(
            'logging_launch.py runs the rosbag2 recorders only; '
            f"the argument(s) {', '.join(stale)} belong to "
            'perception_launch.py (#458) and would be ignored here, leaving '
            "the M3's raw .all archive at its default location.\n\n"
            'Pass them to the perception launch instead, e.g.:\n'
            '  ros2 launch bizzyboat_project11 perception_launch.py '
            f'{stale[0]}:=<value>\n\n'
            'The bag directories, which do live here, are log_directory:= / '
            'log_subdirectory:= and sonar_log_directory:= / '
            'sonar_log_subdirectory:=.')
    return []


# BizzyBoat rosbag2 recorders.
#
# Extracted from perception_launch.py (#458) so recording is its own process
# group: the boat can be up -- cameras, sonar, nav -- without accumulating
# bags, and recording can be stopped and restarted without taking the
# perception chain down with it. Edit the recorder definitions HERE, not in
# perception_launch.py, which no longer carries them.
#
# Run in its own tmux window (see scripts/start_tmux_project11.bash); Ctrl-C
# there sends SIGINT, which rosbag2 needs in order to close its mcap files
# cleanly.
#
# Each launch mints a fresh UTC-stamped subdirectory: rosbag2's recorder
# errors out if its target directory already exists, so a per-invocation
# default is what makes stop-and-restart produce a new bag rather than a
# crash. Pass log_subdirectory:=/sonar_log_subdirectory:= to override.
#
# What each recorder captures is set by the `/**/logger` and
# `/**/sonar_logger` blocks in config/bizzyboat.yaml, loaded below by explicit
# path (not via a group-level SetParametersFromFile); the recorded topic names
# there are absolute, so the namespace push affects only the node names.
def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    # Each recorder can be run without the other -- e.g. stop the sonar bags
    # when disk is tight while diagnostics keep recording.
    logger_enabled = LaunchConfiguration('logger')
    logger_arg = DeclareLaunchArgument(
        'logger', default_value='true',
        description='Record the general (diagnostics/nav) bag.'
    )

    sonar_logger_enabled = LaunchConfiguration('sonar_logger')
    sonar_logger_arg = DeclareLaunchArgument(
        'sonar_logger', default_value='true',
        description='Record the sonar bag (M3 detections, sidescan, etc.).'
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
        # First, so a perception argument stops the launch here rather than
        # part-way into a bring-up that would not have honoured it.
        OpaqueFunction(function=reject_perception_arguments),
        namespace_arg,
        logger_arg,
        sonar_logger_arg,
        log_directory_arg,
        log_subdirectory_arg,
        sonar_log_directory_arg,
        sonar_log_subdirectory_arg,

        GroupAction(
            actions=[
                PushRosNamespace(namespace),

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
                        # emulate_tty below gives rosbag2 a live terminal,
                        # which arms its SPACE-to-pause keyboard handler. This
                        # recorder now sits in an operator-facing tmux window
                        # (#458), where a stray keypress would silently pause
                        # the boat's data of record -- so disable it, the same
                        # reasoning as bag_recorder_operator_launch.py's
                        # --disable-keyboard-controls.
                        {'record.disable_keyboard_controls': True},
                        {'storage.uri': PathJoinSubstitution([
                            log_directory,
                            log_subdirectory
                        ])}
                    ],
                    emulate_tty=True,
                    # The logging window is now the operator's only view of
                    # whether recording is actually running (#458). Default
                    # 'log' would leave it blank -- including on a failed
                    # start -- so send rosbag2's output to the screen too.
                    output='both',
                    # Generous SIGTERM grace so mcap finalization on a large
                    # bag completes after the SIGINT -- same reasoning as
                    # bag_recorder_operator_launch.py on the operator side.
                    sigterm_timeout='15',
                    sigkill_timeout='5',
                    condition=IfCondition(logger_enabled)
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
                        {'record.disable_keyboard_controls': True},
                        {'storage.uri': PathJoinSubstitution([
                            sonar_log_directory,
                            sonar_log_subdirectory
                        ])},
                    ],
                    emulate_tty=True,
                    output='both',
                    sigterm_timeout='15',
                    sigkill_timeout='5',
                    condition=IfCondition(sonar_logger_enabled)
                ),
            ]
        ),
    ])
