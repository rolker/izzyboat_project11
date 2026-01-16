from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    return LaunchDescription([
        DeclareLaunchArgument(
            'num_cameras',
            default_value='4',
            description='Number of cameras to launch (1-4)'
        ),
        DeclareLaunchArgument(
            'active_cameras',
            default_value='1,2,3,4',
            description='List of active cameras (e.g. "1,3" or "1,2,3,4")'
        ),
        DeclareLaunchArgument(
            'enable_video',
            default_value='true',
            description='Enable RGB video stream (true/false)'
        ),
        DeclareLaunchArgument(
            'enable_nn',
            default_value='true',
            description='Enable Neural Network processing (true/false)'
        ),
        DeclareLaunchArgument(
            'preview_width',
            default_value='1280',
            description='Camera preview width'
        ),
        DeclareLaunchArgument(
            'preview_height',
            default_value='720',
            description='Camera preview height'
        ),
        DeclareLaunchArgument(
            'fps',
            default_value='5.0',
            description='Camera FPS'
        ),
        OpaqueFunction(function=launch_setup)
    ])

def launch_setup(context, *args, **kwargs):
    # Retrieve arguments
    active_cameras_str = LaunchConfiguration('active_cameras').perform(context)
    enable_video_str = LaunchConfiguration('enable_video').perform(context)
    enable_nn_str = LaunchConfiguration('enable_nn').perform(context)
    num_cameras_str = LaunchConfiguration('num_cameras').perform(context) # Legacy support

    # Parse boolean flags
    enable_video = enable_video_str.lower() in ['true', '1', 'yes']
    enable_nn = enable_nn_str.lower() in ['true', '1', 'yes']

    # Determine active cameras
    active_indices = []
    
    # Check if active_cameras was explicitly set (not default) or if we should fallback to num_cameras logic
    # Ideally we prioritize active_cameras if valid.
    if active_cameras_str and active_cameras_str.strip():
        try:
            # Parse comma-separated string "1,3" -> [1, 3]
            parts = active_cameras_str.split(',')
            for p in parts:
                val = int(p.strip())
                if 1 <= val <= 4:
                    active_indices.append(val - 1) # Convert 1-based ID to 0-based index
        except ValueError:
            # If any value is not an integer, ignore the parsing error here;
            # the fallback logic below (using num_cameras) will handle this case.
            pass
    
    # Fallback to num_cameras if active_cameras yielded nothing (or user didn't set it and wants legacy behavior)
    # However, 'active_cameras' has a default which overrides 'num_cameras' usually.
    # To support legacy 'num_cameras' arg usage, we could check if active_cameras is default.
    # But let's simplify: active_cameras takes precedence. 
    # If active_cameras is default "1,2,3,4", we use that.
    # If user passed num_cameras:=2, active_cameras is still "1,2,3,4" unless cleared.
    # Let's support num_cameras if active_cameras is default.
    if active_cameras_str == '1,2,3,4' and num_cameras_str != '4':
       active_indices = []
       try:
           cnt = int(num_cameras_str)
           for i in range(cnt):
               if i < 4: active_indices.append(i)
       except ValueError:
           active_indices = [0,1,2,3]

    if not active_indices:
        active_indices = [0,1,2,3]

    all_camera_ids = [
        '194430106121872D00', # Camera 1 (Front Left - 171)
        '19443010D117872D00', # Camera 2 (Front Right - 172)
        '19443010E11A872D00', # Camera 3 (Rear Left - 173)
        '14442C10917D8DD700', # Camera 4 (Rear Right - 174)
    ]

    all_camera_names = [
        'camera_171',
        'camera_172',
        'camera_173',
        'camera_174',
    ]

    # Filter based on active indices
    camera_ids = [all_camera_ids[i] for i in active_indices if i < 4]
    camera_names = [all_camera_names[i] for i in active_indices if i < 4]
    
    blob_path = os.path.join(
        get_package_share_directory('sea_surface_segmentation'),
        'config',
        'ewasr_resnet18.blob'
    )

    fps = LaunchConfiguration('fps')
    preview_width = LaunchConfiguration('preview_width')
    preview_height = LaunchConfiguration('preview_height')

    node = Node(
        package='sea_surface_segmentation',
        executable='sea_surface_segmentation',
        name='sea_surface_segmentation',
        output='screen',
        parameters=[{
            'camera_ids': camera_ids,
            'camera_names': camera_names,
            'neural_network': blob_path,
            'enable_video': enable_video,
            'enable_nn': enable_nn,
            'preview_width': preview_width,
            'preview_height': preview_height,
            'fps': fps
        }]
    )

    return [node]
