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

    return LaunchDescription([
        namespace_arg,
        device_arg,
        baud_arg,
        talker_id_arg,

        GroupAction(
            actions=[
                Node(
                    package='zda_serial_bridge',
                    executable='zda_serial_bridge',
                    name='zda_serial_bridge',
                    parameters=[{
                        'device': device,
                        'baud': baud,
                        'talker_id': talker_id,
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
