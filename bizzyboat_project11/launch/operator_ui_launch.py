from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
  robot_namespace = LaunchConfiguration('robot_namespace')
  operator_namespace = LaunchConfiguration('operator_namespace')
  background_chart = LaunchConfiguration('background_chart')
  diagnostics_rqt = LaunchConfiguration('diagnostics_rqt')
  logger_rqt = LaunchConfiguration('logger_rqt')
  sonar_rqt = LaunchConfiguration('sonar_rqt')

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
  # Extra rqt instances, consolidated here from the tmux session so the whole
  # operator UI comes up from one launch. Toggle off to suppress a window.
  diagnostics_rqt_arg = DeclareLaunchArgument(
    "diagnostics_rqt", default_value="true"
  )
  logger_rqt_arg = DeclareLaunchArgument(
    "logger_rqt", default_value="true"
  )
  sonar_rqt_arg = DeclareLaunchArgument(
    "sonar_rqt", default_value="true"
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

  # Diagnostics rqt (was the 'rqt-diag' tmux window).
  diagnostics_rqt_node = Node(
    package='rqt_gui',
    executable='rqt_gui',
    name='rqt_diagnostics',
    arguments=['-p', 'bizzyboat-diagnostics'],
    condition=IfCondition(diagnostics_rqt),
    respawn=True,
    respawn_delay=5,
    emulate_tty=True
  )

  # Operator log rqt: the 'logger' perspective drives the rqt_operator_log
  # plugin (timeline + rosbag2 recording into /home/field/data/logs/operator).
  logger_rqt_node = Node(
    package='rqt_gui',
    executable='rqt_gui',
    name='rqt_logger',
    arguments=['-p', 'logger'],
    condition=IfCondition(logger_rqt),
    respawn=True,
    respawn_delay=5,
    emulate_tty=True
  )

  # Sonar rqt: the 'bizzy_sonar' perspective for monitoring the sidescan /
  # echogram displays during a survey.
  sonar_rqt_node = Node(
    package='rqt_gui',
    executable='rqt_gui',
    name='rqt_sonar',
    arguments=['-p', 'bizzy_sonar'],
    condition=IfCondition(sonar_rqt),
    respawn=True,
    respawn_delay=5,
    emulate_tty=True
  )

  return LaunchDescription([
    robot_namespace_arg,
    operator_namespace_arg,
    background_chart_arg,
    diagnostics_rqt_arg,
    logger_rqt_arg,
    sonar_rqt_arg,
    launch_operator_ui_include,
    diagnostics_rqt_node,
    logger_rqt_node,
    sonar_rqt_node
  ])
