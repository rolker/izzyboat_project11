#!/usr/bin/env python3
"""
Static sound-speed stand-in for a failed SVS (field stopgap, 2026-06-16).

Replaces the live sound_speed_bridge output with a FIXED value while the AML
SVS / its serial connection is down, so the survey can finish with a constant
(if not live) sound speed. Mirrors what the bridge emits:

  1. Valeport-format UDP to the M3's listener (default mercat:20003): the
     exact ' NNNNNNN\\r\\n' frame the M3 expects (space + 7-digit mm/s + CRLF),
     matching sound_speed_bridge.sinks.format_valeport. THIS is what the M3
     applies for refraction / what lands in the .all.
  2. marine_interfaces/SoundSpeed on /bizzy/sensors/sound_speed/sound_speed
     for ROS consumers/logging (skipped automatically if ROS isn't sourced).

Defaults: 1493.3 m/s at 1 Hz.

  python3 static_sound_speed.py                 # 1493.3 m/s, 1 Hz, both sinks
  python3 static_sound_speed.py --value 1494.0 --rate 1.0
  python3 static_sound_speed.py --no-ros        # UDP to M3 only
  python3 static_sound_speed.py --host mercat --port 20003

Ctrl-C to stop.

*** IMPORTANT: stop this script the moment the real SVS is restored. ***
If the bridge resumes publishing live SV while this is also running, the M3 and
the ROS topic get BOTH the live and the static value interleaved.
"""
import argparse
import socket
import sys
import time


def valeport_frame(value_m_s: float) -> bytes:
    """' NNNNNNN\\r\\n' -- space + 7-digit mm/s + CRLF (M3 Valeport format)."""
    mm_s = round(value_m_s * 1000)
    if mm_s < 0 or mm_s > 9999999:
        raise ValueError(f'value {value_m_s} m/s out of Valeport range')
    return f' {mm_s:7d}\r\n'.encode('ascii')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--value', type=float, default=1493.3, help='sound speed m/s')
    ap.add_argument('--rate', type=float, default=1.0, help='Hz')
    ap.add_argument('--host', default='mercat', help='M3 Valeport UDP host')
    ap.add_argument('--port', type=int, default=20003, help='M3 Valeport UDP port')
    ap.add_argument('--topic', default='/bizzy/sensors/sound_speed/sound_speed')
    ap.add_argument('--frame-id', default='bizzy/sound_speed_sensor')
    ap.add_argument('--no-ros', action='store_true', help='UDP to M3 only')
    ap.add_argument('--no-udp', action='store_true', help='ROS topic only')
    args = ap.parse_args(argv)

    period = 1.0 / args.rate if args.rate > 0 else 1.0
    frame = valeport_frame(args.value)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # ROS sink is optional: degrade to UDP-only if rclpy/msgs aren't on the path.
    node = pub = rclpy = None
    if not args.no_ros:
        try:
            import rclpy as _rclpy
            from marine_interfaces.msg import SoundSpeed
            rclpy = _rclpy
            rclpy.init()
            node = rclpy.create_node('static_sound_speed')
            pub = node.create_publisher(SoundSpeed, args.topic, 10)
            _SoundSpeed = SoundSpeed
        except Exception as exc:  # noqa: B902 - field tool, degrade gracefully
            print(f'[static_sound_speed] ROS sink disabled ({exc}); UDP only',
                  file=sys.stderr)

    targets = []
    if not args.no_udp:
        targets.append(f'UDP {args.host}:{args.port} ({frame!r})')
    if pub is not None:
        targets.append(f'ROS {args.topic}')
    print(f'[static_sound_speed] sending {args.value} m/s @ {args.rate} Hz -> '
          f'{", ".join(targets)}  (Ctrl-C to stop)')

    count = 0
    try:
        while True:
            if not args.no_udp:
                try:
                    sock.sendto(frame, (args.host, args.port))
                except OSError as exc:
                    print(f'[static_sound_speed] UDP send failed: {exc}',
                          file=sys.stderr)
            if pub is not None and rclpy is not None and rclpy.ok():
                msg = _SoundSpeed()
                msg.header.stamp = node.get_clock().now().to_msg()
                msg.header.frame_id = args.frame_id
                msg.sound_speed = float(args.value)
                msg.variance = 0.0
                pub.publish(msg)
            count += 1
            if count % 10 == 1:
                print(f'[static_sound_speed] sent {count} ({args.value} m/s)')
            time.sleep(period)
    except KeyboardInterrupt:
        print(f'\n[static_sound_speed] stopped after {count} sends')
    finally:
        sock.close()
        if node is not None:
            node.destroy_node()
        if rclpy is not None and rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
