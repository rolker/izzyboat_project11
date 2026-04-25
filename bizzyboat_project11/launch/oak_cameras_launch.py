from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


# BizzyBoat OAK camera MXIDs (verified 2026-03-30). Each entry may carry
# optional flags; absent flags fall back to sea_surface_segmentation defaults.
CAMERAS = {
    'oak_forward':   {'mx_id': '19443010D117872D00', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 1000},
    'oak_starboard': {'mx_id': '19443010E11A872D00', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 800},
    'oak_aft':       {'mx_id': '14442C10917D8DD700', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 800},
    'oak_port':      {'mx_id': '194430106121872D00', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 800},
}


def _oak_camera_node(name, cfg):
    params = {
        'camera_ids': [cfg['mx_id']],
        'camera_names': [name],
        'neural_network': PathJoinSubstitution([
            FindPackageShare('sea_surface_segmentation'),
            'config',
            'ewasr_resnet18.blob'
        ]),
    }
    if 'enable_video' in cfg:
        params['enable_video'] = cfg['enable_video']
    if cfg.get('h265_enable'):
        params['h265_enable'] = True
        for opt in ('h265_bitrate_kbps', 'h265_keyframe_frequency_frames', 'h265_profile'):
            if opt in cfg:
                params[opt] = cfg[opt]
    return Node(
        package='sea_surface_segmentation',
        executable='sea_surface_segmentation',
        name=name,
        parameters=[params],
        respawn=True,
        respawn_delay=5,
        emulate_tty=True
    )


def generate_launch_description():
    return LaunchDescription([
        _oak_camera_node(name, cfg)
        for name, cfg in CAMERAS.items()
    ])
