from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


# BizzyBoat OAK camera MXIDs (verified 2026-03-30). Each entry may carry
# optional flags; absent flags fall back to sea_surface_segmentation defaults.
#
# Coprime `h265_keyframe_frequency_frames` (23/29/31/37) decorrelate H.265
# IDR keyframes across cameras so simultaneous IDR bursts don't overrun the
# Starlink uplink (~5 Mbps lossy knee). The depthai v2.x VideoEncoder has
# no GOP-phase offset or runtime forceIntraRequest, so pairwise-coprime
# intervals are the only API-supported decorrelation. Aft has the longest
# GOP since slower error-recovery hurts least on the least-critical view;
# forward (primary nav view) has the shortest. At fps=5 the per-camera
# GOPs are 4.6 / 5.8 / 6.2 / 7.4 s; the joint period (LCM) is ~42 hours,
# so coincidences are effectively eliminated within a single deployment.
#
# Physical remount (2026-07-20): the OAK cameras were reinstalled rotated one
# position (uniform 90 deg). MXIDs are fixed to devices, so each direction slot
# below was reassigned to the device that now actually looks that way. The
# per-view H.265 tuning stays keyed to the direction (view importance), not to
# the device, so only the mx_id values rotated:
#   forward <- was starboard, starboard <- was aft,
#   aft     <- was port,      port      <- was forward.
#
# `h265_bitrate_kbps` 800 -> 100 (all four), field change 2026-08-05 at Lewes,
# DE, paired with the vpn cap 1.5 -> 1.0 MB/s and the collision_pointcloud 1 Hz
# vpn throttle in config/bizzyboat.yaml. Landed in two steps the same session:
# 800 -> 500 first, then the operator set 100 kbps live and confirmed the
# picture "still looks good"; 100 is the field-proven value and is persisted
# here so a relaunch cannot silently revert it.
#
# WHY: the four ffmpeg streams were offering ~404 KB/s of a ~1.27 MB/s total on
# a vpn link that could not carry it. The udp_bridge#43 admission controller
# measured delivery under its 90% threshold, halved repeatedly to its 10% floor,
# and dropped 89-94% of the video. Salmon received 1 keyframe out of ~19 expected
# across the four streams: a keyframe is ~90 bridge fragments, ONE lost fragment
# kills the whole message, so keyframes die first while smaller P-frames survive,
# and the decoder can never resync — that is the garbling mechanism.
#
# MEASURED RESULT at 100 kbps (gabby, 25 s / 13-sample window): vpn admission
# held AT CAP in every sample with zero backoff, aggregate vpn drop 78.4% ->
# 7.7%, oak_forward 101 KB/s at 22.1 fragments/frame and ~90% loss -> 31.6 KB/s
# at 7.3 fragments/frame and 0.0% loss. Note the FRAGMENT COUNT matters as much
# as the bitrate: a ~7-fragment frame is an order of magnitude less exposed to
# the one-lost-fragment failure than a ~90-fragment one, which is why quality
# holds up far better than the 8x bitrate cut alone would suggest.
#
# NB the encoder applies this by RESTARTING the pipeline (camera_base.cpp), so
# each camera drops its stream for a few seconds when the value changes.
# The GOP values below are deliberately NOT shortened: changing two variables at
# once would make the next measurement uninterpretable, and at 100 kbps keyframe
# survival is no longer the binding constraint. Shortening them is the next lever
# only if keyframe loss reappears.
# Do NOT raise this back toward 800 without re-measuring the link — 800 kbps is
# what drove the admission collapse, and the collapse degraded /tf and mavros
# telemetry (~45%) as well as video.
CAMERAS = {
    'oak_forward':   {'mx_id': '19443010E11A872D00', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 100,
                      'h265_keyframe_frequency_frames': 23},
    'oak_starboard': {'mx_id': '14442C10917D8DD700', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 100,
                      'h265_keyframe_frequency_frames': 31},
    'oak_aft':       {'mx_id': '194430106121872D00', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 100,
                      'h265_keyframe_frequency_frames': 37},
    'oak_port':      {'mx_id': '19443010D117872D00', 'enable_video': False,
                      'h265_enable': True, 'h265_bitrate_kbps': 100,
                      'h265_keyframe_frequency_frames': 29},
}


def _oak_camera_node(name, cfg):
    params = {
        'camera_ids': [cfg['mx_id']],
        'camera_names': [name],
        # Match the URDF-published frame in `urdf/sensors/camera_oak.xacro`
        # (`bizzy/<name>_optical`) so the segmentation Image + CameraInfo
        # frame_id resolves in the live TF tree. Without this the publisher
        # falls back to the package default `<name>_optical_frame`, which
        # is not in BizzyBoat's TF tree and breaks any consumer that does
        # a TF lookup against the message header (e.g. SeaSurfaceLayer).
        'frame_ids': [f'bizzy/{name}_optical'],
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
