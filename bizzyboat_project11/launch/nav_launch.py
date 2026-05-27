from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    return LaunchDescription([
        namespace_arg,

        # Nav2
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('echoboat_project11'),
                    'launch',
                    'nav2_bringup_launch.py'
                ])
            ),
            launch_arguments={
                'namespace': namespace,
                'use_namespace': 'true',
                'use_composition': 'false',
                # BizzyBoat is an EchoBoat 240; supply its sensor-rig + reflex
                # overlay on top of the generic base + 240 hull params (seafloor#3).
                'model': '240',
                'instance_params': PathJoinSubstitution([
                    FindPackageShare('bizzyboat_project11'),
                    'config',
                    'nav2_overlay.yaml',
                ]),
            }.items()
        ),

        # Republish a cropped, smaller window of the local costmap for the
        # operator (CAMP) over the lossy bridge — unh_marine_navigation#38,
        # unh_marine_autonomy#127. Runs in the local_costmap namespace so it
        # subscribes to <ns>/local_costmap/costmap and publishes
        # <ns>/local_costmap/costmap_windowed. window_size is live-tunable.
        Node(
            package='marine_nav_utilities',
            executable='costmap_window_node',
            name='costmap_window',
            namespace=[namespace, '/local_costmap'],
            parameters=[{'window_size': 200.0}],
            output='screen',
        ),
    ])
