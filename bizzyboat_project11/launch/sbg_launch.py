from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value='bizzy'
    )

    sbg_config = PathJoinSubstitution([
        FindPackageShare('bizzyboat_project11'),
        'config',
        'sbg_ellipse_d.yaml'
    ])

    return LaunchDescription([
        namespace_arg,
        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                PushRosNamespace('sensors'),

                # SBG INS driver. Subscribes to RTCM via the remapping below
                # so it shares /bizzy/sensors/rtcm with rtcm_relay. The
                # `sensors` namespace (not `sensors/sbg`) leaves the
                # driver's internal `sbg/` topic prefix to land output
                # topics at /bizzy/sensors/sbg/<name> instead of the
                # doubled /bizzy/sensors/sbg/sbg/<name>.
                Node(
                    package='sbg_driver',
                    executable='sbg_device',
                    name='sbg_device',
                    parameters=[sbg_config],
                    remappings=[
                        ('ntrip_client/rtcm', 'rtcm'),
                    ],
                    respawn=True,
                    respawn_delay=5,
                    emulate_tty=True
                ),

                # mavros_msgs/RTCM (FCU NTRIP feed) -> rtcm_msgs/Message.
                Node(
                    package='bizzyboat_project11',
                    executable='rtcm_relay_node.py',
                    name='rtcm_relay',
                    parameters=[{
                        'input_topic': ['/', namespace, '/mavros/gps_rtk/send_rtcm'],
                        'output_topic': 'rtcm',
                    }],
                    respawn=True,
                    respawn_delay=5,
                    emulate_tty=True
                ),
            ]
        )
    ])
