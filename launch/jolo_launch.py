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
                    'jolo_hd.yaml'
                ])
            }.items()
        ),
        Node(
            package='buoy_projector',
            executable='buoy_projector',
            name='buoy_projector',
            remappings=[
                ('input_detections', 'izzy/jolo/nn/detections'),
                ('camera_info', 'jolo/nn/passthrough/camera_info'),
                ('output_detections', 'izzy/jolo/nn/detections_3d')
            ],
            parameters=[{
                'map_frame': 'izzy/map_tide'
            }]
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
            package="image_transport",
            executable="republish",
            name="detection_visualizer_compressor",
            remappings=[
                ('in', 'izzy/jolo/nn/detections/image_raw'),
                ('out/compressed', 'izzy/jolo/nn/detections/image_raw/compressed'),
            ],
            parameters=[{
                'out_transport': "compressed"
            }]
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


