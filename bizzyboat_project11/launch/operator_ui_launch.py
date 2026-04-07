from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
  robot_namespace = LaunchConfiguration('robot_namespace')
  operator_namespace = LaunchConfiguration('operator_namespace')
  background_chart = LaunchConfiguration('background_chart')

  robot_namespace_arg = DeclareLaunchArgument(
    "robot_namespace", default_value=TextSubstitution(text="bizzy")
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
        FindPackageShare('marine_autonomy'),
        'launch',
        'operator_ui_launch.py'
      ])
    ),
    launch_arguments={
      'robot_namespace': robot_namespace,
      'operator_namespace': operator_namespace,
      'background_chart': background_chart,
      'rqt': 'true',
      'rqt_perspective': 'bizzyboat'
    }.items()
  )

  return LaunchDescription([
    robot_namespace_arg,
    operator_namespace_arg,
    background_chart_arg,
    launch_operator_ui_include
  ])
