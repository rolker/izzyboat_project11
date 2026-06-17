#!/usr/bin/env python3
"""
Temperature-derived sound-speed feed for a failed SVS (field stopgap, 2026-06-16).

Computes sound speed live from the Garmin sidescan's water-temperature telemetry
and feeds it where the dead AML SVS used to, so the survey tracks the actual
water as it changes (better than a fixed static value):

    SV = Marczak1997_freshwater(T) + offset

- Marczak (1997) is the distilled-water freshwater equation (0-95 C).
- ``offset`` (default +0.96 m/s) is the empirical SVS-minus-Marczak(temp)
  correction measured from bag bizzyboat/2026-06-16T15-54-20+00-00 (SVS mean
  1491.79 @ 22.88 C vs Marczak 1490.87; paired mean +0.96, std 0.65). It folds
  in the lake's dissolved-solids excess over distilled water + sensor calibration.

Outputs (same sinks as the bridge, both at --rate Hz):
  1. Valeport-format UDP to the M3 (default mercat:20003): ' NNNNNNN\\r\\n'
  2. marine_interfaces/SoundSpeed on /bizzy/sensors/sound_speed/sound_speed

Requires ROS sourced (it subscribes to the Garmin temperature topic).

  python3 temp_sound_speed.py                       # offset +0.96, 1 Hz, both sinks
  python3 temp_sound_speed.py --offset 0.96 --rate 1.0
  python3 temp_sound_speed.py --fallback 1492.3     # used until/if temp is unavailable

Ctrl-C to stop.

*** Stop this the moment the real SVS is restored (else live + derived interleave). ***
*** Needs the Garmin sidescan transmitting (that's where the temperature comes from). ***
"""
import argparse
import socket
import sys

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Temperature
from marine_interfaces.msg import SoundSpeed


def marczak_freshwater(T: float) -> float:
    """Marczak 1997 distilled-water sound speed (m/s), T in deg C, valid 0-95 C."""
    return (1402.385 + 5.038813 * T - 5.799136e-2 * T**2 + 3.287156e-4 * T**3
            - 1.398845e-6 * T**4 + 2.787860e-9 * T**5)


def valeport_frame(value_m_s: float):
    """' NNNNNNN\\r\\n' -- space + 7-digit mm/s + CRLF (M3 Valeport format)."""
    mm_s = round(value_m_s * 1000)
    if mm_s < 0 or mm_s > 9999999:
        return None
    return f' {mm_s:7d}\r\n'.encode('ascii')


class TempSoundSpeed(Node):
    def __init__(self, args):
        super().__init__('temp_sound_speed')
        self.args = args
        self._T = None            # latest temperature, deg C
        self._T_t = None          # monotonic time of latest temperature
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._n = 0
        be = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(Temperature, args.temp_topic, self._on_temp, be)
        self._pub = None if args.no_ros else self.create_publisher(
            SoundSpeed, args.ss_topic, 10)
        self.create_timer(1.0 / args.rate if args.rate > 0 else 1.0, self._tick)
        self.get_logger().info(
            f'temp_sound_speed: SV = Marczak(T) {args.offset:+.3f}, @{args.rate} Hz '
            f'-> UDP {args.host}:{args.port}{"" if args.no_ros else " + ROS "+args.ss_topic}; '
            f'temp from {args.temp_topic}; fallback {args.fallback} m/s')

    def _on_temp(self, msg):
        T = float(msg.temperature)
        if T == T and -5.0 < T < 50.0:        # finite + sane
            self._T = T
            self._T_t = self.get_clock().now().nanoseconds * 1e-9

    def _tick(self):
        now = self.get_clock().now().nanoseconds * 1e-9
        if self._T is not None:
            age = now - self._T_t
            sv = marczak_freshwater(self._T) + self.args.offset
            src = f'T={self._T:.2f}C age={age:.0f}s'
            if age > self.args.stale_after:
                self.get_logger().warn(
                    f'temperature stale ({age:.0f}s > {self.args.stale_after:.0f}s) '
                    f'- is the Garmin transmitting? using last T',
                    throttle_duration_sec=10.0)
        else:
            sv = float(self.args.fallback)
            src = 'no temp yet -> fallback'

        if not self.args.no_udp:
            frame = valeport_frame(sv)
            if frame is not None:
                try:
                    self._sock.sendto(frame, (self.args.host, self.args.port))
                except OSError as exc:
                    self.get_logger().warn(f'UDP send failed: {exc}',
                                           throttle_duration_sec=10.0)
        if self._pub is not None:
            m = SoundSpeed()
            m.header.stamp = self.get_clock().now().to_msg()
            m.header.frame_id = self.args.frame_id
            m.sound_speed = float(sv)
            m.variance = 0.0
            self._pub.publish(m)

        self._n += 1
        if self._n % 10 == 1:
            self.get_logger().info(f'SV={sv:.2f} m/s  ({src})')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--offset', type=float, default=0.96,
                    help='SV - Marczak(T) correction, m/s (bag-measured +0.96)')
    ap.add_argument('--rate', type=float, default=1.0, help='Hz')
    ap.add_argument('--host', default='mercat', help='M3 Valeport UDP host')
    ap.add_argument('--port', type=int, default=20003, help='M3 Valeport UDP port')
    ap.add_argument('--temp-topic',
                    default='/bizzy/sensors/sidescan/garmin_sidescan/water_temperature')
    ap.add_argument('--ss-topic', default='/bizzy/sensors/sound_speed/sound_speed')
    ap.add_argument('--frame-id', default='bizzy/sound_speed_sensor')
    ap.add_argument('--fallback', type=float, default=1492.3,
                    help='SV to send until a temperature arrives')
    ap.add_argument('--stale-after', type=float, default=30.0,
                    help='warn if temperature older than this (s)')
    ap.add_argument('--no-ros', action='store_true')
    ap.add_argument('--no-udp', action='store_true')
    args = ap.parse_args(argv)

    rclpy.init()
    node = TempSoundSpeed(args)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\n[temp_sound_speed] stopped', file=sys.stderr)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
