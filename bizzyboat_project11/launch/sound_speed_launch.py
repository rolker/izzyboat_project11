"""Sound-speed bridge launch for BizzyBoat.

AML SVS on gabby /dev/ttyS0 -> ROS topic + Valeport-format UDP fan-out to
M3 (mercat:20003). The driver is in the rolker/marine_tools repo as the
sound_speed_bridge package.

Wiring: AML SVS is RX-only (the probe just emits sound-velocity sentences;
nothing is sent back to it), so it lives on gabby's ttyS0 even though
ttyS0's TX line driver is dead — that fault is irrelevant to this device.
The SBG, which needs bidirectional comms for ECom + RTCM, owns ttyS1.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.substitutions import LaunchConfiguration
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace


def generate_launch_description():
    frame_prefix = LaunchConfiguration('frame_prefix')
    frame_prefix_arg = DeclareLaunchArgument(
        'frame_prefix', default_value='bizzy/'
    )

    device = LaunchConfiguration('device')
    device_arg = DeclareLaunchArgument(
        'device', default_value=TextSubstitution(text='/dev/ttyS0')
    )

    baud = LaunchConfiguration('baud')
    baud_arg = DeclareLaunchArgument('baud', default_value='9600')

    return LaunchDescription([
        frame_prefix_arg,
        device_arg,
        baud_arg,

        GroupAction(
            actions=[
                # Topics land at /<namespace>/sensors/sound_speed/<topic>
                # (sound_speed, temperature, fluid_pressure) — matches the
                # /<ns>/sensors/<sensor>/<topic> convention used by the
                # SBG, deltat, ntrip, and oak camera nodes.
                PushRosNamespace('sensors/sound_speed'),
                Node(
                    package='sound_speed_bridge',
                    executable='sound_speed_bridge',
                    name='sound_speed_bridge',
                    parameters=[{
                        'device': device,
                        'baud': baud,
                        'parser': 'aml',
                        'frame_id': [frame_prefix, 'sound_speed_sensor'],
                        # Valeport-format UDP to M3 (built-in Valeport listener on mercat).
                        # Replaces the interim PowerShell stand-in (aml_bridge.ps1).
                        'udp_hosts': ['mercat'],
                        'udp_ports': [20003],
                        'udp_formats': ['valeport'],
                        'udp_templates': [''],
                    }],
                    respawn=True,
                    respawn_delay=2.0,
                    emulate_tty=True
                ),
            ]
        ),
    ])
