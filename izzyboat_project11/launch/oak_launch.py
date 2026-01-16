from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def launch_setup(context, *args, **kwargs):
    camera_id = LaunchConfiguration('id').perform(context)
    
    # Map IDs to camera config
    # 1 -> 171
    # 2 -> 172
    # 3 -> 173
    # 4 -> 174
    
    cameras = {
        '1': {'name': 'camera_171', 'mx_id': '194430106121872D00'},
        '2': {'name': 'camera_172', 'mx_id': '19443010D117872D00'},
        '3': {'name': 'camera_173', 'mx_id': '19443010E11A872D00'},
        '4': {'name': 'camera_174', 'mx_id': '14442C10917D8DD700'}
    }

    if camera_id not in cameras:
        raise ValueError(f"Invalid camera ID: {camera_id}. Must be 1, 2, 3, or 4.")
    
    cam = cameras[camera_id]

    blob_path = PathJoinSubstitution([
        FindPackageShare('sea_surface_segmentation'),
        'config',
        'ewasr_resnet18.blob'
    ])

    # Pass as single-item lists
    node = Node(
        package='sea_surface_segmentation',
        executable='sea_surface_segmentation',
        name=cam['name'], # keeping node name specific if running individually
        output='screen',
        parameters=[{
            'camera_ids': [cam['mx_id']],
            'camera_names': [cam['name']],
            'neural_network': blob_path
        }]
    )

    return [node]

def generate_launch_description():
    id_arg = DeclareLaunchArgument(
        'id',
        default_value='1',
        description='Camera ID (1-4) to launch'
    )

    return LaunchDescription([
        id_arg,
        OpaqueFunction(function=launch_setup)
    ])
