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
        Node(
            package = 'detection_visualizer',
            executable = 'detection_visualizer',
            name = 'detection_visualizer',
            remappings = [
                ('detection_visualizer/detections', 'izzy/jolo/nn/detections'),
                ('detection_visualizer/images', 'izzy/jolo/nn/passthrough/image_raw'),
                ('detection_visualizer/dbg_images', 'izzy/jolo/nn/detections/image_raw'),

            ]
        ),
        Node(
            package="topic_tools",
            executable="throttle",
            name="throttle_jolo",
            arguments=['message',],
            parameters=[{
                'input_topic':'izzy/jolo/nn/passthrough/image_raw/compressed',
                'output_topic': 'izzy/jolo/nn/passthrough/image_raw/throttled/compressed',
                'throttle_type': 'messages',
                'msgs_per_sec': 1.0
            }]
        ),
        Node(
            package="topic_tools",
            executable="throttle",
            name="throttle_jolo_detection_images",
            arguments=['message',],
            parameters=[{
                'input_topic':'izzy/jolo/nn/detections/image_raw',
                'output_topic': 'izzy/jolo/nn/detections/image_raw/throttled/image_raw',
                'throttle_type': 'messages',
                'msgs_per_sec': 1.0
            }]
        ),

    ])


