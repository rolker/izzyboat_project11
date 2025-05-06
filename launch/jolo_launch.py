import os

from launch import LaunchDescription
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import SetParameter
from launch_ros.actions import SetRemap
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
                'name': "forward_oak",
                'params_file': PathJoinSubstitution([
                    FindPackageShare('izzyboat_project11'),
                    'config',
                    'jolo_hd.yaml'
                ])
            }.items()
        ),
        GroupAction(
            actions = [
                SetParameter(
                    name = 'map_frame',
                    value = 'izzy/map_tide'
                ),
                SetRemap(
                    src = 'input_detections',
                    dst = 'izzy/forward_oak/nn/detections'
                ),
                SetRemap(
                    src = 'camera_info',
                    dst = 'izzy/forward_oak/nn/passthrough/camera_info'
                ),
                SetRemap(
                    src = 'output_detections',
                    dst = 'izzy/forward_oak/nn/detections_3d'
                ),    
                IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                    FindPackageShare('buoy_projector'),
                    'launch',
                    'buoy_projector_launch.py'
                    ])
                ),
                )
            ]
        ),
        Node(
            package = 'detection_visualizer',
            executable = 'detection_visualizer',
            name = 'detection_visualizer',
            remappings = [
                ('detection_visualizer/detections', 'izzy/forward_oak/nn/detections'),
                ('detection_visualizer/images', 'izzy/forward_oak/nn/passthrough/image_raw'),
                ('detection_visualizer/dbg_images', 'izzy/forward_oak/nn/detections/image_raw'),

            ]
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="detection_visualizer_compressor",
            remappings=[
                ('in', 'izzy/forward_oak/nn/detections/image_raw'),
                ('out/compressed', 'izzy/forward_oak/nn/detections/image_raw/compressed'),
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
                'input_topic':'izzy/forward_oak/nn/passthrough/image_raw/compressed',
                'output_topic': 'izzy/forward_oak/nn/passthrough/image_raw/throttled/compressed',
                'throttle_type': 'messages',
                'msgs_per_sec': 0.5
            }]
        ),
        Node(
            package="topic_tools",
            executable="throttle",
            name="throttle_jolo_detection_images",
            arguments=['message',],
            parameters=[{
                'input_topic':'izzy/forward_oak/nn/detections/image_raw/compressed',
                'output_topic': 'izzy/forward_oak/nn/detections/image_raw/throttled/compressed',
                'throttle_type': 'messages',
                'msgs_per_sec': 0.5
            }]
        ),

    ])


