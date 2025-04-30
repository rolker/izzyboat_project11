import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

# Jenna's Only Look Once (JOLO)


def generate_launch_description():

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('depthai_ros_driver'),
                    'launch',
                    'camera.launch.py'
                ])
            ),
            launch_arguments={
                'name': "jolo",
                'params_file': PathJoinSubstitution([
                    FindPackageShare('izzyboat_project11'),
                    'config',
                    'jolo.yaml'
                ])
            }.items()
        ),
    ])


