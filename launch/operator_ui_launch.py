from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import SetParameter
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
  robot_namespace = LaunchConfiguration('robot_namespace')
  operator_namespace = LaunchConfiguration('operator_namespace')
  background_chart = LaunchConfiguration('background_chart')

  robot_namespace_arg = DeclareLaunchArgument(
    "robot_namespace", default_value=TextSubstitution(text="izzy")
  )
  operator_namespace_arg = DeclareLaunchArgument(
    "operator_namespace", default_value=TextSubstitution(text="operator")
  )
  background_chart_arg = DeclareLaunchArgument(
    "background_chart", default_value=PathJoinSubstitution(
      [FindPackageShare('camp'), 'workspace', '13283', '13283_2.KAP']
    )
  )

  launch_operator_ui_include = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
      PathJoinSubstitution([
        FindPackageShare('project11'),
        'launch',
        'operator_ui_launch.py'
      ])
    ),
    launch_arguments={
      'robot_namespace': robot_namespace,
      'operator_namespace': operator_namespace,
      'background_chart': background_chart,
      'rviz': 'true',
      'rviz_configuration': PathJoinSubstitution([
        FindPackageShare('izzyboat_project11'),
        'config',
        'izzyboat.rviz'
      ]),
      'rqt': 'true',
      'rqt_perspective': 'izzyboat'
    }.items()
  )

  return LaunchDescription([
    robot_namespace_arg,
    operator_namespace_arg,
    background_chart_arg,
    launch_operator_ui_include
  ])

# <launch>
#   <arg name="namespace" default="operator"/>
#   <arg name="robotNamespace" default="izzy"/>
#   <arg name="backgroundChart" default="$(find camp)/workspace/13283/13283_2.KAP"/>
#   <arg name="dual_camp" default="false"/>

#   <include file="$(find project11)/launch/operator_ui.launch">
#     <arg name="namespace" value="$(arg namespace)"/>
#     <arg name="robotNamespace" value="$(arg robotNamespace)"/>
#     <arg name="backgroundChart" value="$(arg backgroundChart)"/>
#     <arg name="rqt" value="false"/>
#     <arg name="dual_camp" value="$(arg dual_camp)"/>
#   </include>

#   <!-- <node pkg="rqt_gui" type="rqt_gui" name="rqt-cameras" args="-p izzyboat_cameras"/> -->

#   <node type="rviz" name="rviz_izzy" pkg="rviz" args="-d $(find izzyboat_project11)/config/izzyboat.rviz"/> 
# </launch>

