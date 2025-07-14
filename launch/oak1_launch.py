import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.actions import OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParameter
from launch_ros.actions import SetRemap
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
                'frame_id': 'izzy/forward_oak_camera_optical_frame',
                'yolo_blob_path': PathJoinSubstitution([
                    FindPackageShare('sea_surface_segmentation'),
                    'config',
                    '1280x704_yolov5_model4_3_openvino_2022.1_6shave.blob'
                ]),
                'yolo_width': 1280,
                'yolo_height': 704,
                'yolo_confidence_threshold': 0.5,
                'yolo_number_of_classes': 2,
                'yolo_anchors': [10.0, 13.0, 16.0, 30.0, 33.0, 23.0, 30.0, 61.0, 62.0, 45.0, 59.0, 119.0, 116.0, 90.0, 156.0, 198.0, 373.0, 326.0],
                'yolo_anchor_mask_labels': ['side160', 'side80', 'side40'],
                'yolo_anchor_masks.side160': [0, 1, 2],
                'yolo_anchor_masks.side80': [3, 4, 5],
                'yolo_anchor_masks.side40': [6, 7, 8],
                'yolo_iou_threshold': 0.5,
            }],
            respawn = True,
            respawn_delay = 5
        ),
        Node(
            package="topic_tools",
            executable="throttle",
            name="throttle_jolo",
            arguments=['message',],
            parameters=[{
                'input_topic':'oak/segmentation/passthrough/image_raw/compressed',
                'output_topic': 'oak/segmentation/passthrough/image_raw/throttled/compressed',
                'throttle_type': 'messages',
                'msgs_per_sec': 0.5
            }]
        ),
        GroupAction(
            actions = [
                PushRosNamespace("oak"),
                SetParameter(
                    name = 'map_frame',
                    value = 'izzy/map_tide'
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare('sea_surface_segmentation'),
                            'launch',
                            'segments_to_pointcloud_launch.py'
                        ])
                    ),
                )

            ]
        ),
        GroupAction(
            actions = [
                SetParameter(
                    name = 'map_frame',
                    value = 'izzy/map_tide'
                ),
                SetRemap(
                    src = 'input_detections',
                    dst = 'oak/detections'
                ),
                SetRemap(
                    src = 'camera_info',
                    dst = 'oak/detections/passthrough/camera_info'
                ),
                SetRemap(
                    src = 'output_detections',
                    dst = 'oak/detections_3d'
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
        # Node(
        #     package = 'detection_visualizer',
        #     executable = 'detection_visualizer',
        #     name = 'detection_visualizer',
        #     remappings = [
        #         ('detection_visualizer/detections', 'oak/detections'),
        #         ('detection_visualizer/images', 'oak/detections/passthrough/image_raw'),
        #         ('detection_visualizer/dbg_images', 'oak/detections/image_raw'),

        #     ]
        # ),
        # Node(
        #     package="image_transport",
        #     executable="republish",
        #     name="detection_visualizer_compressor",
        #     remappings=[
        #         ('in', 'oak/detections/image_raw'),
        #         ('out/compressed', 'oak/detections/image_raw/compressed'),
        #     ],
        #     parameters=[{
        #         'out_transport': "compressed"
        #     }]
        # ),
        # Node(
        #     package="topic_tools",
        #     executable="throttle",
        #     name="throttle_jolo",
        #     arguments=['message',],
        #     parameters=[{
        #         'input_topic':'oak/detections/passthrough/image_raw/compressed',
        #         'output_topic': 'oak/detections/passthrough/image_raw/throttled/compressed',
        #         'throttle_type': 'messages',
        #         'msgs_per_sec': 0.5
        #     }]
        # ),
        # Node(
        #     package="topic_tools",
        #     executable="throttle",
        #     name="throttle_jolo_detection_images",
        #     arguments=['message',],
        #     parameters=[{
        #         'input_topic':'oak/detections/image_raw/compressed',
        #         'output_topic': 'oak/detections/image_raw/throttled/compressed',
        #         'throttle_type': 'messages',
        #         'msgs_per_sec': 0.5
        #     }]
        # ),

    ])


