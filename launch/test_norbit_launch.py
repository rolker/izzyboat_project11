from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from launch_ros.actions import SetParametersFromFile
from launch_ros.actions import SetRemap
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    namespace = LaunchConfiguration('namespace')

    namespace_arg = DeclareLaunchArgument(
      "namespace", default_value=TextSubstitution(text="izzy")
    )

    frame_prefix = LaunchConfiguration('frame_prefix')

    frame_prefix_arg = DeclareLaunchArgument(
        "frame_prefix", default_value="izzy/"
    )


    return LaunchDescription([
      namespace_arg,
      frame_prefix_arg,
      GroupAction(
          actions=[
            PushRosNamespace(namespace),
            SetParametersFromFile(
              filename=PathJoinSubstitution([
                  FindPackageShare('izzyboat_project11'),
                  'config',
                  'izzyboat.yaml'
              ])                
            ),
            GroupAction(
                actions=[
                  PushRosNamespace('sensors/norbit'),
                  IncludeLaunchDescription(
                      PythonLaunchDescriptionSource(
                          PathJoinSubstitution([
                              FindPackageShare('norbit_driver'),
                              'launch',
                              'norbit_launch.py'
                          ])
                      )
                  ),
                  IncludeLaunchDescription(
                      PythonLaunchDescriptionSource(
                          PathJoinSubstitution([
                              FindPackageShare('cube_bathymetry'),
                              'launch',
                              'cube_bathymetry_launch.py'
                          ])
                      )
                  ),
                ]
            ),
            GroupAction(
              actions=[
                  PushRosNamespace('sensors/posmv'),
                  IncludeLaunchDescription(
                      PythonLaunchDescriptionSource(
                          PathJoinSubstitution([
                              FindPackageShare('posmv'),
                              'launch',
                              'posmv_launch.py'
                          ])
                      )
                  )
              ]      
            ),

          ]
      ),


    ])

