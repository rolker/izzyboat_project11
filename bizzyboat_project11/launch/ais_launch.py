from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParametersFromFile
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Bring up the AIS decode chain.

    The three nodes talk to each other over RELATIVE topic names, so pushing
    them into a shared `ais` namespace wires them together without a single
    remap:

        nmea_relay          -> <ns>/ais/nmea      (raw !AIVDM sentences)
        ais_parser          -> <ns>/ais/messages  (decoded AIS messages)
        ais_contact_tracker -> <ns>/ais/contacts  (per-MMSI AISContact)

    `<ns>/ais/contacts` is what ais_layer subscribes to; see the ais_layer
    blocks in nav2_overlay.yaml, which name it explicitly.

    marine_ais_tools ships its own ais_parser_with_nmea_relay.launch.py, but it
    omits ais_contact_tracker entirely (relay + parser only) and remaps to a
    different topic layout, so it cannot produce the contacts the costmap layer
    needs. This launch is the boat's own composition rather than an include.
    """
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    return LaunchDescription([
        namespace_arg,

        GroupAction(
            actions=[
                # Push ONLY the sub-namespace. This launch is included from
                # core_launch.py inside a GroupAction that has already pushed
                # the robot namespace, and PushRosNamespace nests: pushing it
                # again here put the nodes at /bizzy/bizzy/ais/... while
                # ais_layer subscribed to /bizzy/ais/contacts, so the layers had
                # zero publishers and the costmap never saw a contact.
                # Matches sidescan_launch.py, which likewise pushes only
                # 'sensors/sidescan'. The namespace argument is kept because
                # callers pass it, and so this file reads the same as its
                # siblings.
                PushRosNamespace('ais'),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'ais.yaml'
                    ])
                ),

                # respawn on all three: a crashed relay/parser/tracker would
                # otherwise silently erase the traffic picture until relaunch
                # (degrade-to-no-AIS is safe for nav, but must not be silent
                # AND permanent).

                # Shore receiver -> UDP 2125 -> Sentence messages.
                Node(
                    package='marine_ais_tools',
                    executable='nmea_relay',
                    name='nmea_relay',
                    emulate_tty=True,
                    respawn=True,
                    respawn_delay=5.0
                ),

                # Sentences -> decoded AIS messages.
                Node(
                    package='marine_ais_tools',
                    executable='ais_parser',
                    name='ais_parser',
                    emulate_tty=True,
                    respawn=True,
                    respawn_delay=5.0
                ),

                # AIS messages -> one AISContact per MMSI, carrying pose,
                # velocity, hull footprint and the covariances ais_layer needs.
                Node(
                    package='marine_ais_tools',
                    executable='ais_contact_tracker',
                    name='ais_contact_tracker',
                    emulate_tty=True,
                    respawn=True,
                    respawn_delay=5.0
                ),
            ]
        ),
    ])
