from launch import LaunchDescription
from launch.actions import GroupAction
from launch_ros.actions import Node
from launch_ros.actions import PushRosNamespace


# Forward USB camera (generic UVC "HD USB Camera" on /dev/video0).
#
# Extracted from perception_launch.py so the full stack and the cameras-only
# test launch (camera_test_launch.py) share a single definition -- edit the
# camera config HERE, not in either includer. Include this under the
# `sensors/cameras` namespace (as perception_launch.py does) so the node lands
# at <ns>/sensors/cameras/usb/usb_camera, matching the udp_bridge topic config
# in bizzyboat.yaml.
def generate_launch_description():
    return LaunchDescription([
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
                        # Device ("HD USB Camera", /dev/video0)
                        # offers MJPG at 640x480 but NOT 640x360.
                        # Requesting an unsupported 360 made the
                        # driver fall back to 640x480 capture
                        # while still framing for 360 -> mjpeg2rgb
                        # produced all-zero (pure black) buffers.
                        # 480 matches a supported mode. (v4l2-ctl
                        # --list-formats-ext on gabby, 2026-06-03)
                        'image_height': 480,
                        'frame_id': 'bizzy/usb_camera_optical',
                        'pixel_format': 'mjpeg2rgb',
                        # ffmpeg_image_transport (3.0.2) encoder
                        # config for the image_raw/ffmpeg topic.
                        # Unlike the OAKs (H.265 on-device via the
                        # depthai VideoEncoder), this generic UVC
                        # cam has no onboard encoder, so we encode
                        # H.265 in software on the host. CPU cost
                        # is negligible at 640x480 @ 5 fps. Mirrors
                        # the OAK 800 kbps budget; gop_size 41 is
                        # coprime with the OAK keyframe intervals
                        # (23/29/31/37) so its IDR bursts don't
                        # coincide with theirs on the uplink.
                        # Alternative for host-GPU offload:
                        # encoder 'hevc_nvenc'. (Param names
                        # verified against the live node:
                        # ffmpeg_image_transport's publisher param
                        # is `encoder`, NOT `encoding` -- the latter
                        # is the FFMPEGPacket message field.)
                        'image_raw.ffmpeg.encoder': 'libx265',
                        'image_raw.ffmpeg.bit_rate': 800000,
                        'image_raw.ffmpeg.gop_size': 41,
                    }],
                    emulate_tty=True
                ),
            ]
        ),
    ])
