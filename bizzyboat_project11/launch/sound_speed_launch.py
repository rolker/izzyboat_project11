"""Sound-speed bridge launch for BizzyBoat.

AML SVS on gabby /dev/ttyS1 -> ROS topic + Valeport-format UDP fan-out to
M3 (mercat:20003). The driver is in the rolker/marine_tools repo as the
sound_speed_bridge package.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    frame_prefix = LaunchConfiguration('frame_prefix')
    frame_prefix_arg = DeclareLaunchArgument(
        'frame_prefix', default_value='bizzy/'
    )

    device = LaunchConfiguration('device')
    device_arg = DeclareLaunchArgument(
        'device', default_value=TextSubstitution(text='/dev/ttyS1')
    )

    baud = LaunchConfiguration('baud')
    baud_arg = DeclareLaunchArgument('baud', default_value='9600')

    return LaunchDescription([
        frame_prefix_arg,
        device_arg,
        baud_arg,

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
    ])
