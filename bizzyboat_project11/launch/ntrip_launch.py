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
            ]
        )
    ])
