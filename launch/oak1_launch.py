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



def generate_launch_description():

    return LaunchDescription([
        Node(
            package = "sea_surface_segmentation",
            executable = "sea_surface_segmentation",
            name = "sea_surface_segmentation",
            parameters = [{
                'neural_network': PathJoinSubstitution([
                    FindPackageShare('sea_surface_segmentation'),
                    'config',
                    'ewasr_resnet18.blob'
                ]),
            }]
        )
    ])


