from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParametersFromFile
from launch_ros.substitutions import FindPackageShare


# Cameras-only bring-up for bench / dockside perception testing.
#
# Brings up ONLY the camera nodes (USB forward cam + 4 OAKs) and the UDP
# bridge, so the cameras can be exercised and streamed to the operator station
# without launching the rest of the stack (no sonar, nav, mavros, loggers).
# Namespacing, the bizzyboat.yaml param set, and the included camera launches
# are identical to perception_launch.py / core_launch.py, so topic names match
# the udp_bridge config in bizzyboat.yaml.
#
# Requires the zenoh router to be up first (rmw_zenoh_cpp); the companion
# scripts/start_tmux_camera_test.bash starts zenohd before this launch.
#
# Toggles:  usb:=false   oak:=false   to bring up only a subset.
def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    usb = LaunchConfiguration('usb')
    usb_arg = DeclareLaunchArgument('usb', default_value='true')

    oak = LaunchConfiguration('oak')
    oak_arg = DeclareLaunchArgument('oak', default_value='true')

    bridge = LaunchConfiguration('bridge')
    bridge_arg = DeclareLaunchArgument('bridge', default_value='true')

    pkg = FindPackageShare('bizzyboat_project11')

    return LaunchDescription([
        namespace_arg,
        usb_arg,
        oak_arg,
        bridge_arg,

        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        pkg, 'config', 'bizzyboat.yaml'
                    ])
                ),

                # Cameras (same nesting as perception_launch.py)
                GroupAction(
                    actions=[
                        PushRosNamespace('sensors/cameras'),

                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    pkg, 'launch', 'usb_camera_launch.py'
                                ])
                            ),
                            condition=IfCondition(usb)
                        ),

                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    pkg, 'launch', 'oak_cameras_launch.py'
                                ])
                            ),
                            condition=IfCondition(oak)
                        ),
                    ]
                ),

                # UDP bridge (same include as core_launch.py; reads the
                # /**/udp_bridge block from bizzyboat.yaml set above)
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('udp_bridge'),
                            'launch',
                            'udp_bridge_launch.py'
                        ])
                    ),
                    condition=IfCondition(bridge)
                ),
            ]
        ),
    ])
