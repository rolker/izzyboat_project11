from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParametersFromFile
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    operator_namespace = LaunchConfiguration('operator_namespace')

    operator_namespace_arg = DeclareLaunchArgument(
      "operator_namespace", default_value=TextSubstitution(text="operator")
    )

    robot_namespace = LaunchConfiguration('robot_namespace')

    robot_namespace_arg = DeclareLaunchArgument(
      "robot_namespace", default_value=TextSubstitution(text="izzy")
    )

    enable_bridge = LaunchConfiguration('enable_bridge')
    enable_bridge_arg = DeclareLaunchArgument(
        "enable_bridge", default_value="true"
    )

    return LaunchDescription([
        operator_namespace_arg,
        robot_namespace_arg,
        enable_bridge_arg,
        GroupAction(
            actions=[
                PushRosNamespace(operator_namespace),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('izzyboat_project11'),
                        'config',
                        'operator.yaml'
                    ])                
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('udp_bridge'),
                        'launch',
                        'udp_bridge_launch.py'
                    ])
                    ),
                    condition = IfCondition(enable_bridge)
                )
            ]
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('project11'),
                    'launch',
                    'operator_core_launch.py'
                ])
            ),
            launch_arguments={
            'operator_namespace': operator_namespace,
            'robot_namespace': robot_namespace,
            'enable_bridge': 'false',
            'operator_joystick': 'true'
            }.items()
        )

    ])


# <launch>
#   <arg name="namespace" default="operator"/>
#   <arg name="robotNamespace" default="izzy"/>
#   <arg name="enableBridge" default="true"/>
#   <arg name="robotHost" default="dora"/>
  

#   <include file="$(find echoboat_project11)/launch/operator_echo.launch">
#     <arg name="namespace" value="$(arg namespace)"/>
#     <arg name="robotNamespace" value="$(arg robotNamespace)"/>
#     <arg name="enableBridge" value="$(arg enableBridge)"/>
#   </include>

#   <include file="$(find izzyboat_project11)/launch/load_urdf.launch">
#     <arg name="namespace" value="$(arg robotNamespace)"/>
#   </include>

#   <group ns="$(arg namespace)">
#     <rosparam param="udp_bridge/remotes/robot/connections/default/host" subst_value="True">"$(arg robotHost)"</rosparam>

#   </group>

# </launch>



