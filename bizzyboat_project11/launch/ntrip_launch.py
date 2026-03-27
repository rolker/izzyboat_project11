from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    namespace = LaunchConfiguration('namespace')

    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value='bizzy'
    )

    return LaunchDescription([
        namespace_arg,
        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                SetRemap(
                    src='rtcm',
                    dst=['/', namespace, '/mavros/gps_rtk/send_rtcm']
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('ntrip_client'),
                            'launch',
                            'ntrip_client_launch.py'
                        ])
                    ),
                    launch_arguments={
                        'namespace': 'sensors/ntrip',
                        'host': 'macorsrtk.massdot.state.ma.us',
                        'port': '31000',
                        'mountpoint': 'RTCM3_MASA',
                        'username': 'bizzyboat',
                        'password': 'bizzyboat',
                        'rtcm_message_package': 'mavros_msgs',
                    }.items()
                ),
            ]
        )
    ])
