from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    namespace = LaunchConfiguration('namespace')

    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value='bizzy'
    )

    ntrip_credentials = PathJoinSubstitution([
        FindPackageShare('ccomjhc_project11'),
        'configuration',
        'bizzyboat_ntrip.yaml'
    ])

    return LaunchDescription([
        namespace_arg,
        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                SetRemap(
                    src='rtcm',
                    dst=['/', namespace, '/mavros/gps_rtk/send_rtcm']
                ),

                # GGA echoback throttle. Network/iMAX NTRIP mountpoints
                # require the rover to publish GGA back so the caster can
                # compute the virtual base. mavros's NavSatFix is ~10 Hz —
                # well above what casters expect (0.1–1 Hz) — so we throttle
                # before feeding ntrip_client. The output topic name lines
                # up with the relative `fix` subscription that
                # ntrip_ros_base.py:101 creates inside the ntrip_client node.
                Node(
                    package='topic_tools',
                    executable='throttle',
                    name='gga_throttle',
                    arguments=[
                        'messages',
                        ['/', namespace, '/mavros/global_position/raw/fix'],
                        '1.0',
                        ['/', namespace, '/sensors/ntrip/fix'],
                    ],
                ),

                Node(
                    name='ntrip_client',
                    namespace='sensors/ntrip',
                    package='ntrip_client',
                    executable='ntrip_ros.py',
                    respawn=True,
                    respawn_delay=5,
                    emulate_tty=True,
                    parameters=[
                        ntrip_credentials,
                        {
                            'rtcm_message_package': 'mavros_msgs',
                            'rtcm_frame_id': 'odom',
                            'nmea_max_length': 128,
                            'nmea_min_length': 3,
                            'reconnect_attempt_max': 10,
                            'reconnect_attempt_wait_seconds': 5,
                            'rtcm_timeout_seconds': 4,
                        }
                    ],
                ),

                # RTCM diagnostics: liveness (the 'NTRIP' status, unchanged
                # from the retired ntrip_diagnostics_node) plus correction
                # PROVENANCE -- which base station and how far away. The
                # credentials YAML is passed so the caster host/port/mountpoint
                # actually in force appear in the diagnostic; the password in
                # that file is never declared by the node and so never read.
                Node(
                    package='bizzyboat_project11',
                    executable='rtcm_diagnostics_node.py',
                    name='rtcm_diagnostics',
                    # Same policy as the ntrip_client above it: a diagnostics
                    # node that dies stops publishing, and a missing status
                    # reads as health on the annunciator. Restart it.
                    respawn=True,
                    respawn_delay=5,
                    parameters=[
                        ntrip_credentials,
                        {
                            'rtcm_topic': 'mavros/gps_rtk/send_rtcm',
                            'rtcm_message_package': 'mavros_msgs',
                            'fix_topic': 'mavros/global_position/global',
                            'liveness_diagnostic_name': 'NTRIP',
                            'provenance_diagnostic_name': 'RTK: corrections',
                            'warn_timeout': 5.0,
                            'error_timeout': 15.0,
                            # MaCORS serves this berth from station 42 at
                            # 27.4 km, so 35 km is a working headroom for NH
                            # operations; past 100 km a reported fix should not
                            # be believed at all (the Delaware caster that hid
                            # here for 18 days was 509 km).
                            'warn_baseline_km': 35.0,
                            'error_baseline_km': 100.0,
                        }
                    ],
                    emulate_tty=True
                ),
            ]
        )
    ])
