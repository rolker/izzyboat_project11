#!/usr/bin/env python3
"""Publish GPS RTK fix type as a ROS diagnostic.

Subscribes to a mavros GPSRAW topic and publishes a DiagnosticStatus
with human-readable fix type and configurable severity thresholds.

The status is published on *every* tick, including before any GPSRAW has
arrived and after the topic goes quiet. Reporting nothing when the input is
missing turns a fault into an absence, and an absent status reads as health on
the annunciator -- the failure mode that hid a dead RTK path on 2026-08-20.

Note what this diagnostic can and cannot see: ``fix_type`` is the receiver's
own opinion of its solution. A receiver working from a base station hundreds of
kilometres away will happily report RTK Fixed while its vertical wanders by
metres. Correction *provenance* -- which base, how far -- is
``rtcm_diagnostics_node.py``'s job, and the two belong together.
"""

import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from mavros_msgs.msg import GPSRAW


# Map fix_type integer to human-readable label.
FIX_TYPE_LABELS = {
    0: 'No GPS',
    1: 'No Fix',
    2: '2D Fix',
    3: '3D Fix',
    4: 'DGPS',
    5: 'RTK Float',
    6: 'RTK Fixed',
    7: 'Static',
    8: 'PPP',
}


def accuracy_text(millimetres):
    """Format a GPSRAW accuracy field, or say it is not being reported.

    h_acc/v_acc are MAVLink GPS_RAW_INT *extension* fields. A receiver or a
    mavros build that does not populate them leaves them zero, and zero
    formatted as metres is '0.000' -- millimetre-perfect accuracy, published
    from a receiver that said nothing at all. That is the same failure this
    node exists to prevent, one field down.
    """
    if millimetres <= 0:
        return 'not reported'
    return f'{millimetres / 1000.0:.3f}'


class GpsRtkDiagnosticsNode(Node):

    def __init__(self):
        super().__init__('gps_rtk_diagnostics')

        self.declare_parameter('gps_raw_topic', 'mavros/gpsstatus/gps1/raw')
        self.declare_parameter('diagnostic_name', 'GPS: RTK')
        self.declare_parameter('hardware_id', '')
        # Minimum fix_type for OK level (default: RTK Fixed = 6)
        self.declare_parameter('ok_min_fix_type', 6)
        # Minimum fix_type for WARN level (default: 3D Fix = 3)
        self.declare_parameter('warn_min_fix_type', 3)
        # Seconds without a GPSRAW message before the status goes stale
        self.declare_parameter('stale_timeout', 5.0)

        self._topic = self.get_parameter('gps_raw_topic').value
        self._diagnostic_name = self.get_parameter('diagnostic_name').value
        self._hardware_id = self.get_parameter('hardware_id').value
        self._ok_min = self.get_parameter('ok_min_fix_type').value
        self._warn_min = self.get_parameter('warn_min_fix_type').value
        self._stale_timeout = self.get_parameter('stale_timeout').value

        self._last_msg = None
        self._last_msg_time = None

        self._pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self._sub = self.create_subscription(GPSRAW, self._topic, self._on_gps_raw, 10)
        self._timer = self.create_timer(1.0, self._publish_diagnostic)

        self.get_logger().info(
            f'Publishing RTK diagnostics from "{self._topic}" as "{self._diagnostic_name}" '
            f'(OK >= {self._ok_min}, WARN >= {self._warn_min})'
        )

    def _on_gps_raw(self, msg: GPSRAW):
        self._last_msg = msg
        self._last_msg_time = self.get_clock().now()

    def _publish_diagnostic(self):
        now = self.get_clock().now()
        status = DiagnosticStatus()
        status.name = self._diagnostic_name
        status.hardware_id = self._hardware_id

        if self._last_msg is None:
            # Never heard from the receiver. Say so loudly rather than
            # publishing nothing.
            status.level = DiagnosticStatus.ERROR
            status.message = f'no data on "{self._topic}"'
            status.values = [
                KeyValue(key='gps_raw_topic', value=str(self._topic)),
                # Present on every other path, so anything keying off it does
                # not have to treat 'missing' and 'no data' as separate cases.
                KeyValue(key='fix_type', value='-1'),
            ]
            self._publish(status, now)
            return

        msg = self._last_msg
        age = (now - self._last_msg_time).nanoseconds / 1e9
        fix_type = msg.fix_type
        label = FIX_TYPE_LABELS.get(fix_type, f'Unknown ({fix_type})')

        if age > self._stale_timeout:
            # A frozen fix_type is worse than none: it reports the last good
            # state forever.
            status.level = DiagnosticStatus.STALE
            status.message = f'stale: no update for {age:.0f}s (last {label})'
        elif fix_type >= self._ok_min:
            status.level = DiagnosticStatus.OK
            status.message = label
        elif fix_type >= self._warn_min:
            status.level = DiagnosticStatus.WARN
            status.message = label
        else:
            status.level = DiagnosticStatus.ERROR
            status.message = label

        status.values = [
            KeyValue(key='fix_type', value=str(fix_type)),
            KeyValue(key='satellites_visible', value=str(msg.satellites_visible)),
            KeyValue(key='eph', value=str(msg.eph)),
            KeyValue(key='epv', value=str(msg.epv)),
            # Vertical accuracy is the quantity tide and soundings depend on,
            # and it degrades long before fix_type does.
            KeyValue(key='h_acc_m', value=accuracy_text(msg.h_acc)),
            KeyValue(key='v_acc_m', value=accuracy_text(msg.v_acc)),
            KeyValue(key='age_s', value=f'{age:.1f}'),
        ]
        self._publish(status, now)

    def _publish(self, status, now):
        array = DiagnosticArray()
        array.header.stamp = now.to_msg()
        array.status = [status]
        self._pub.publish(array)


def main(args=None):
    rclpy.init(args=args)
    node = GpsRtkDiagnosticsNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
