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
                # driver's internal `sbg/` topic prefix to land the
                # proprietary output topics at /bizzy/sensors/sbg/<name>
                # instead of the doubled /bizzy/sensors/sbg/sbg/<name>.
                #
                # The driver's ros_standard publishers use an `imu/` prefix
                # (imu/data, imu/nav_sat_fix, imu/velocity, ...) which would
                # land them at /bizzy/sensors/imu/<name> — ambiguous against
                # any other IMU and split from the rest of the SBG output.
                # Remap each under `sbg/` so ALL SBG topics (proprietary and
                # standard) group under /bizzy/sensors/sbg/. The standard
                # topics had no consumers (mru_transform still reads mavros),
                # so this rename is safe; the proprietary `sbg/<name>` topics
                # are unchanged (zda_launch consumes sbg/utc_time by name).
                Node(
                    package='sbg_driver',
                    executable='sbg_device',
                    name='sbg_device',
                    parameters=[sbg_config],
                    remappings=[
                        ('ntrip_client/rtcm', 'rtcm'),
                        ('imu/data', 'sbg/imu/data'),
                        ('imu/nav_sat_fix', 'sbg/imu/nav_sat_fix'),
                        ('imu/velocity', 'sbg/imu/velocity'),
                        ('imu/mag', 'sbg/imu/mag'),
                        ('imu/temp', 'sbg/imu/temp'),
                        ('imu/pos_ecef', 'sbg/imu/pos_ecef'),
                        ('imu/utc_ref', 'sbg/imu/utc_ref'),
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
