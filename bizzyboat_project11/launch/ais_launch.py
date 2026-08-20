from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.substitutions import LaunchConfiguration
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
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    return LaunchDescription([
        namespace_arg,

        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                PushRosNamespace('ais'),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'ais.yaml'
                    ])
                ),

                # Shore receiver -> UDP 2125 -> Sentence messages.
                Node(
                    package='marine_ais_tools',
                    executable='nmea_relay',
                    name='nmea_relay',
                    emulate_tty=True
                ),

                # Sentences -> decoded AIS messages.
                Node(
                    package='marine_ais_tools',
                    executable='ais_parser',
                    name='ais_parser',
                    emulate_tty=True
                ),

                # AIS messages -> one AISContact per MMSI, carrying pose,
                # velocity, hull footprint and the covariances ais_layer needs.
                Node(
                    package='marine_ais_tools',
                    executable='ais_contact_tracker',
                    name='ais_contact_tracker',
                    emulate_tty=True
                ),
            ]
        ),
    ])
