#!/usr/bin/env python3
"""Publish GPS RTK fix type as a ROS diagnostic.

Subscribes to a mavros GPSRAW topic and publishes a DiagnosticStatus
with human-readable fix type and configurable severity thresholds.
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

        topic = self.get_parameter('gps_raw_topic').value
        self._diagnostic_name = self.get_parameter('diagnostic_name').value
        self._hardware_id = self.get_parameter('hardware_id').value
        self._ok_min = self.get_parameter('ok_min_fix_type').value
        self._warn_min = self.get_parameter('warn_min_fix_type').value

        self._pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self._sub = self.create_subscription(GPSRAW, topic, self._on_gps_raw, 10)

        self.get_logger().info(
            f'Publishing RTK diagnostics from "{topic}" as "{self._diagnostic_name}" '
            f'(OK >= {self._ok_min}, WARN >= {self._warn_min})'
        )

    def _on_gps_raw(self, msg: GPSRAW):
        fix_type = msg.fix_type
        label = FIX_TYPE_LABELS.get(fix_type, f'Unknown ({fix_type})')

        if fix_type >= self._ok_min:
            level = DiagnosticStatus.OK
        elif fix_type >= self._warn_min:
            level = DiagnosticStatus.WARN
        else:
            level = DiagnosticStatus.ERROR

        status = DiagnosticStatus()
        status.level = level
        status.name = self._diagnostic_name
        status.message = label
        status.hardware_id = self._hardware_id
        status.values = [
            KeyValue(key='fix_type', value=str(fix_type)),
            KeyValue(key='satellites_visible', value=str(msg.satellites_visible)),
            KeyValue(key='eph', value=str(msg.eph)),
        ]

        array = DiagnosticArray()
        array.header.stamp = self.get_clock().now().to_msg()
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
