#!/usr/bin/env python3
"""Publish NTRIP connection status as a ROS diagnostic.

Monitors the RTCM topic from the NTRIP client. If messages stop
arriving, escalates from OK to WARN to ERROR based on configurable
timeouts.
"""

import rclpy
from rclpy.node import Node
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from mavros_msgs.msg import RTCM


class NtripDiagnosticsNode(Node):

    def __init__(self):
        super().__init__('ntrip_diagnostics')

        self.declare_parameter('rtcm_topic', 'sensors/ntrip/rtcm')
        self.declare_parameter('diagnostic_name', 'NTRIP')
        self.declare_parameter('hardware_id', '')
        # Seconds without RTCM before WARN
        self.declare_parameter('warn_timeout', 5.0)
        # Seconds without RTCM before ERROR
        self.declare_parameter('error_timeout', 15.0)
        # Diagnostic publish rate (Hz)
        self.declare_parameter('publish_rate', 1.0)

        topic = self.get_parameter('rtcm_topic').value
        self._diagnostic_name = self.get_parameter('diagnostic_name').value
        self._hardware_id = self.get_parameter('hardware_id').value
        self._warn_timeout = self.get_parameter('warn_timeout').value
        self._error_timeout = self.get_parameter('error_timeout').value
        rate = self.get_parameter('publish_rate').value

        self._last_rtcm_time = None
        self._msg_count = 0

        self._pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self._sub = self.create_subscription(RTCM, topic, self._on_rtcm, 10)
        self._timer = self.create_timer(1.0 / rate, self._publish_diagnostic)

        self.get_logger().info(
            f'Monitoring NTRIP via "{topic}" as "{self._diagnostic_name}" '
            f'(WARN after {self._warn_timeout}s, ERROR after {self._error_timeout}s)'
        )

    def _on_rtcm(self, msg: RTCM):
        self._last_rtcm_time = self.get_clock().now()
        self._msg_count += 1

    def _publish_diagnostic(self):
        now = self.get_clock().now()

        if self._last_rtcm_time is None:
            age = -1.0
            level = DiagnosticStatus.ERROR
            message = 'no data received'
        else:
            age = (now - self._last_rtcm_time).nanoseconds / 1e9
            if age > self._error_timeout:
                level = DiagnosticStatus.ERROR
                message = f'no data for {age:.0f}s'
            elif age > self._warn_timeout:
                level = DiagnosticStatus.WARN
                message = f'no data for {age:.0f}s'
            else:
                level = DiagnosticStatus.OK
                message = 'receiving corrections'

        status = DiagnosticStatus()
        status.level = level
        status.name = self._diagnostic_name
        status.message = message
        status.hardware_id = self._hardware_id
        status.values = [
            KeyValue(key='messages_received', value=str(self._msg_count)),
            KeyValue(key='last_rtcm_age_s', value=f'{age:.1f}'),
        ]

        array = DiagnosticArray()
        array.header.stamp = now.to_msg()
        array.status = [status]
        self._pub.publish(array)


def main(args=None):
    rclpy.init(args=args)
    node = NtripDiagnosticsNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
