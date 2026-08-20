"""AIS ingest for the operator station: udp/2125 -> ROS -> CAMP.

The feed arrives as raw NMEA over UDP from the shore receiver, and CAMP does
not read UDP — it scans the graph once a second for any topic of type
marine_ais_msgs/AISContact and subscribes to what it finds
(camp/ais/ais_manager.cpp:18-43). Three nodes bridge the gap:

    udp/2125 -> nmea_relay -> ais/raw -> ais_parser -> ais/messages
             -> ais_contact_tracker -> ais/contacts (AISContact) -> CAMP

marine_ais_tools ships ais_parser_with_nmea_relay.launch.py, but it covers only
the middle two nodes and its parameters default to a serial input on
/dev/ttyACM0, so it stops one hop short of the topic CAMP wants and listens on
the wrong thing. This launch supplies the UDP parameters and the third node.

Because CAMP discovers by message type rather than by name, the topic names
here are free; they are namespaced under ais/ for tidiness, not to satisfy a
subscriber.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    ais_port = LaunchConfiguration('ais_port')
    ais_port_arg = DeclareLaunchArgument(
        'ais_port', default_value='2125',
        description='UDP port the shore AIS receiver streams NMEA to.'
    )

    ais_log_directory = LaunchConfiguration('ais_log_directory')
    ais_log_directory_arg = DeclareLaunchArgument(
        'ais_log_directory', default_value='',
        description='Optional directory for nmea_relay to log raw sentences '
                    'to. Empty disables logging.'
    )

    nmea_relay = Node(
        package='marine_ais_tools',
        executable='nmea_relay',
        name='nmea_relay',
        parameters=[{
            'frame_id': 'ais',
            'input_type': 'udp',
            # nmea_relay declares input_port as an int; a launch argument
            # arrives as a string, and rclpy rejects the type mismatch
            # before the node's own int() cast can run.
            'input_port': ParameterValue(ais_port, value_type=int),
            'log_directory': ais_log_directory,
        }],
        remappings=[('nmea', 'ais/raw')],
        output='both',
        respawn=True,
        respawn_delay=5,
    )

    ais_parser = Node(
        package='marine_ais_tools',
        executable='ais_parser',
        name='ais_parser',
        remappings=[
            ('nmea', 'ais/raw'),
            ('messages', 'ais/messages'),
        ],
        output='both',
    )

    # The hop marine_ais_tools' own launch file omits: turns per-message AIS
    # reports into the per-vessel AISContact that CAMP plots.
    ais_contact_tracker = Node(
        package='marine_ais_tools',
        executable='ais_contact_tracker',
        name='ais_contact_tracker',
        remappings=[
            ('messages', 'ais/messages'),
            ('contacts', 'ais/contacts'),
            ('atons', 'ais/atons'),
        ],
        output='both',
    )

    return LaunchDescription([
        ais_port_arg,
        ais_log_directory_arg,
        nmea_relay,
        ais_parser,
        ais_contact_tracker,
    ])
