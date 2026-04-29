#!/usr/bin/env python3
"""Relay RTCM corrections from mavros_msgs/RTCM to rtcm_msgs/Message.

The NTRIP client publishes mavros_msgs/RTCM directly to the FCU's mavros
gps_rtk plugin. The SBG ROS 2 driver expects rtcm_msgs/Message instead.
Same RTCM3 payload, different package and field name. This node copies
each incoming message to the SBG-flavored topic so the same NTRIP stream
can feed both receivers.
"""

import rclpy
from rclpy.node import Node
from mavros_msgs.msg import RTCM as MavrosRTCM
from rtcm_msgs.msg import Message as RtcmMessage


class RtcmRelayNode(Node):

    def __init__(self):
        super().__init__('rtcm_relay')

        self.declare_parameter('input_topic', '/bizzy/mavros/gps_rtk/send_rtcm')
        self.declare_parameter('output_topic', 'rtcm')

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value

        self._pub = self.create_publisher(RtcmMessage, output_topic, 10)
        self._sub = self.create_subscription(
            MavrosRTCM, input_topic, self._on_rtcm, 10
        )

        self.get_logger().info(
            f'Relaying RTCM: "{input_topic}" (mavros_msgs/RTCM) '
            f'-> "{output_topic}" (rtcm_msgs/Message)'
        )

    def _on_rtcm(self, msg: MavrosRTCM):
        out = RtcmMessage()
        out.header = msg.header
        out.message = msg.data
        self._pub.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = RtcmRelayNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
