"""ZDA serial bridge launch for BizzyBoat.

SBG SbgUtcTime -> NMEA $GPZDA on gabby /dev/ttyS2 -> M3 sonar serial input.
Driver lives in the rolker/marine_tools repo as the zda_serial_bridge
package. Output is gated on the SBG's clock_utc_status so the M3 never
gets a wrong wall-clock during cold-start.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.substitutions import LaunchConfiguration
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value='bizzy'
    )

    # Argument names are prefixed `zda_` so this launch composes cleanly
    # alongside sound_speed_launch.py. ROS 2 launch's LaunchConfiguration
    # namespace is global within a launch tree, so a bare `device`/`baud`
    # arg here would inherit whatever an earlier-included launch already
    # declared (sound_speed_launch declares `device` defaulting to
    # /dev/ttyS0).
    device = LaunchConfiguration('zda_device')
    device_arg = DeclareLaunchArgument(
        'zda_device', default_value=TextSubstitution(text='/dev/ttyS2')
    )

    baud = LaunchConfiguration('zda_baud')
    baud_arg = DeclareLaunchArgument('zda_baud', default_value='9600')

    talker_id = LaunchConfiguration('zda_talker_id')
    talker_id_arg = DeclareLaunchArgument(
        'zda_talker_id', default_value='GP')

    # Safety gating knobs — see zda_serial_bridge/node.py for semantics
    # (default min_utc_status=2 means UTC valid + leap-second almanac
    # downloaded; require_utc_sync=False means status-only gating,
    # without also requiring PPS sync).
    min_utc_status = LaunchConfiguration('zda_min_utc_status')
    min_utc_status_arg = DeclareLaunchArgument(
        'zda_min_utc_status', default_value='2')

    require_utc_sync = LaunchConfiguration('zda_require_utc_sync')
    require_utc_sync_arg = DeclareLaunchArgument(
        'zda_require_utc_sync', default_value='false')

    return LaunchDescription([
        namespace_arg,
        device_arg,
        baud_arg,
        talker_id_arg,
        min_utc_status_arg,
        require_utc_sync_arg,

        GroupAction(
            actions=[
                Node(
                    package='zda_serial_bridge',
                    executable='zda_serial_bridge',
                    name='zda_serial_bridge',
                    # Wrap typed substitutions with ParameterValue so
                    # rclpy's strict type check doesn't reject the
                    # string form of the LaunchConfiguration result.
                    # See marine_tools#9 (commit bf99fae) for the same
                    # fix on the underlying package launch file.
                    parameters=[{
                        'device': device,
                        'baud': ParameterValue(baud, value_type=int),
                        'talker_id': talker_id,
                        'min_utc_status': ParameterValue(
                            min_utc_status, value_type=int),
                        'require_utc_sync': ParameterValue(
                            require_utc_sync, value_type=bool),
                    }],
                    remappings=[
                        ('utc_time',
                         ['/', namespace, '/sensors/sbg/utc_time']),
                    ],
                    respawn=True,
                    respawn_delay=2.0,
                    emulate_tty=True
                ),
            ]
        ),
    ])
