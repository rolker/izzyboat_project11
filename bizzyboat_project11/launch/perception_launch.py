import datetime

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import TextSubstitution
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace
from launch_ros.actions import SetParametersFromFile
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    namespace_arg = DeclareLaunchArgument(
        'namespace', default_value=TextSubstitution(text='bizzy')
    )

    log_directory = LaunchConfiguration('log_directory')
    log_directory_arg = DeclareLaunchArgument('log_directory')

    sonar_log_directory = LaunchConfiguration('sonar_log_directory')
    sonar_log_directory_arg = DeclareLaunchArgument(
        'sonar_log_directory',
        default_value=TextSubstitution(text='/home/field/project11/logs/bizzyboat_sonar')
    )
    sonar_log_directory_arg = DeclareLaunchArgument(
        'sonar_log_directory',
        default_value=EnvironmentVariable(
            'P11_SONAR_LOG_DIR',
            default_value='/home/field/data/logs/bizzyboat_sonar'
        )
    )      
    datetime_str = datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec='seconds').replace(':', '-')
    sonar_log_subdirectory = LaunchConfiguration('sonar_log_subdirectory')
    sonar_log_subdirectory_arg = DeclareLaunchArgument(
        'sonar_log_subdirectory',
        default_value=TextSubstitution(text=datetime_str)
    )

    return LaunchDescription([
        namespace_arg,
        log_directory_arg,
        sonar_log_directory_arg,
        sonar_log_subdirectory_arg,

        GroupAction(
            actions=[
                PushRosNamespace(namespace),
                SetParametersFromFile(
                    filename=PathJoinSubstitution([
                        FindPackageShare('bizzyboat_project11'),
                        'config',
                        'bizzyboat.yaml'
                    ])
                ),

                # DeltaT sonar + cube bathymetry
                GroupAction(
                    actions=[
                        PushRosNamespace('sensors/deltat'),
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('imagenex_deltat'),
                                    'launch',
                                    'deltat_launch.py'
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

                # Cameras
                GroupAction(
                    actions=[
                        PushRosNamespace('sensors/cameras'),

                        # USB camera
                        GroupAction(
                            actions=[
                                PushRosNamespace('usb/'),
                                Node(
                                    package='usb_cam',
                                    executable='usb_cam_node_exe',
                                    name='usb_camera',
                                    parameters=[{
                                        'camera_name': 'usb_camera',
                                        'framerate': 5.0,
                                        'image_width': 640,
                                        'image_height': 360,
                                        'frame_id': 'bizzy/usb_camera_optical',
                                        'pixel_format': 'mjpeg2rgb',
                                    }],
                                    emulate_tty=True
                                ),
                            ]
                        ),

                        # 4x OAK cameras
                        IncludeLaunchDescription(
                            PythonLaunchDescriptionSource(
                                PathJoinSubstitution([
                                    FindPackageShare('bizzyboat_project11'),
                                    'launch',
                                    'oak_cameras_launch.py'
                                ])
                            ),
                        ),
                    ]
                ),

                # Rosbag logger
                Node(
                    package='rosbag2_transport',
                    executable='recorder',
                    name='logger',
                    parameters=[
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'config',
                            'bizzyboat.yaml'
                        ]),
                        {'storage.uri': log_directory}
                    ],
                    emulate_tty=True
                ),

                # Sonar logger
                Node(
                    package='rosbag2_transport',
                    executable='recorder',
                    name='sonar_logger',
                    parameters=[
                        PathJoinSubstitution([
                            FindPackageShare('bizzyboat_project11'),
                            'config',
                            'bizzyboat.yaml'
                        ]),
                        {'storage.uri': PathJoinSubstitution([
                            sonar_log_directory,
                            sonar_log_subdirectory
                        ])},
                    ],
                    emulate_tty=True
                ),
            ]
        ),
    ])
