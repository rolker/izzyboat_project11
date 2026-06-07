"""Garmin GCV-20 sidescan launch for BizzyBoat.

The garmin_sidescan driver (rolker/marine_tools) runs on gabby, but the GCV-20
lives on the Garmin Marine Network reachable only from mercat (Windows). On
mercat, ``garmin_sidescan/tools/garmin_marine_network_proxy.ps1`` (in the
marine_tools repo) relays the GCV's imagery multicast + TCP control onto gabby's
LAN; install it as a Windows service with the sibling
``tools/install_proxy_service.ps1``. The proxy defaults already match this boat
(``--gcv-ip 172.16.3.0``, ``--listen-ip 192.168.20.8``, ``--relay-to
192.168.20.5``). So on gabby the driver points at the proxy, not the GCV:

* ``gcv_ip`` = 192.168.20.8  (mercat's bridge NIC = the relay's source address)
* ``iface_ip`` = 192.168.20.5  (gabby's LAN NIC that the imagery is unicast to)

Transmit is OFF at startup and interlocked on a valid sound speed
(``/bizzy/sensors/sound_speed/sound_speed``, published by sound_speed_launch.py).
TF frames for the channels come from ben_description (garmin_sidescan_*).

For the first wet run, set ``debug_raw:=true`` to also record the raw GCV streams
(needed for the offline depth-field decode that the imagery alone can't verify).
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

    # Point at the mercat proxy, not the GCV directly (see module docstring).
    gcv_ip = LaunchConfiguration('gcv_ip')
    gcv_ip_arg = DeclareLaunchArgument(
        'gcv_ip', default_value=TextSubstitution(text='192.168.20.8')
    )

    iface_ip = LaunchConfiguration('iface_ip')
    iface_ip_arg = DeclareLaunchArgument(
        'iface_ip', default_value=TextSubstitution(text='192.168.20.5')
    )

    debug_raw = LaunchConfiguration('debug_raw')
    debug_raw_arg = DeclareLaunchArgument(
        'debug_raw', default_value='false',
        description='Publish raw GCV UDP payloads for offline re-decode '
                    '(set true for the first wet run to capture depth bytes)'
    )

    return LaunchDescription([
        frame_prefix_arg,
        gcv_ip_arg,
        iface_ip_arg,
        debug_raw_arg,

        GroupAction(
            actions=[
                # Topics land at /<namespace>/sensors/sidescan/garmin_sidescan/...
                # matching the /<ns>/sensors/<sensor>/... convention used by the
                # SBG, deltat, sound_speed, and oak camera nodes.
                PushRosNamespace('sensors/sidescan'),
                Node(
                    package='garmin_sidescan',
                    executable='garmin_sidescan',
                    name='garmin_sidescan',
                    parameters=[{
                        'gcv_ip': gcv_ip,
                        'iface_ip': iface_ip,
                        'frame_id': [frame_prefix, 'garmin_sidescan'],
                        'debug_raw': debug_raw,
                        # SAFE: never transmit on startup; only ping under a
                        # valid sound speed from the AML SVS bridge.
                        'transmit_on_startup': False,
                        'sound_speed_safety_enabled': True,
                        'sound_speed_topic':
                            '/bizzy/sensors/sound_speed/sound_speed',
                    }],
                    respawn=True,
                    respawn_delay=2.0,
                    emulate_tty=True,
                ),
            ]
        ),
    ])
