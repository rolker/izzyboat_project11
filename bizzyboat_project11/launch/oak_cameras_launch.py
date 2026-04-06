from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


# BizzyBoat OAK camera MXIDs (verified 2026-03-30)
CAMERAS = {
    'oak_forward':   '19443010D117872D00',
    'oak_starboard': '19443010E11A872D00',
    'oak_aft':       '14442C10917D8DD700',
    'oak_port':      '194430106121872D00',
}


def _oak_camera_node(name, mx_id):
    return Node(
        package='sea_surface_segmentation',
        executable='sea_surface_segmentation',
        name=name,
        parameters=[{
            'camera_ids': [mx_id],
            'camera_names': [name],
            'neural_network': PathJoinSubstitution([
                FindPackageShare('sea_surface_segmentation'),
                'config',
                'ewasr_resnet18.blob'
            ]),
        }],
        respawn=True,
        respawn_delay=5,
        emulate_tty=True
    )


def generate_launch_description():
    return LaunchDescription([
        _oak_camera_node(name, mx_id)
        for name, mx_id in CAMERAS.items()
    ])
