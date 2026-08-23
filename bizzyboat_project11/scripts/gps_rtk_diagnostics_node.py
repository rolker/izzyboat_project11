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


# MAVLink GPS_RAW_INT sentinels. eph/epv are DOP scaled by 100 and
# satellites_visible is a count; all three use UINT16_MAX / 255 for 'unknown'.
UINT16_MAX = 65535
UINT8_MAX = 255


def dop_text(raw):
    """Format eph/epv as a DOP, or say it is unknown.

    Published raw, HDOP 1.21 reads '121' and an unpopulated field reads
    '65535' -- the same class of defect accuracy_text() was written to
    prevent, one field along. Anyone eyeballing the tile sees a number either
    way and has no way to tell which.
    """
    if raw in (0, UINT16_MAX):
        return 'unknown'
    return f'{raw / 100.0:.2f}'


def satellite_text(raw):
    """Satellite count, or 'unknown' for the 255 sentinel."""
    if raw == UINT8_MAX:
        return 'unknown'
    return str(raw)


def validate_thresholds(ok_min, warn_min):
    """Reject a threshold pair that makes a level unreachable.

    warn_min > ok_min silently deletes the WARN branch: every fix_type either
    clears ok_min or falls through to ERROR, so a degraded fix shows red and
    the operator learns to ignore red.
    """
    if warn_min > ok_min:
        raise ValueError(
            f'warn_min_fix_type ({warn_min}) must not exceed ok_min_fix_type '
            f'({ok_min}); as given, the WARN level is unreachable and a '
            f'degraded fix reports ERROR')


def validate_stale_timeout(stale_timeout, publish_period):
    """A timeout shorter than the publish period can never be satisfied."""
    if stale_timeout < publish_period:
        raise ValueError(
            f'stale_timeout ({stale_timeout} s) is shorter than the publish '
            f'period ({publish_period} s), so every status would be born '
            f'stale')


def accuracy_m(millimetres):
    """h_acc/v_acc in metres, or ``None`` when the receiver is not reporting it.

    The numeric counterpart of accuracy_text, so the level and the key it is
    published under cannot disagree about what zero means.
    """
    if millimetres <= 0:
        return None
    return millimetres / 1000.0


def classify_fix(fix_type, ok_min, warn_min):
    """Map a GPSRAW fix_type to ``(level, message)``."""
    label = FIX_TYPE_LABELS.get(fix_type, f'Unknown ({fix_type})')
    if fix_type >= ok_min:
        return DiagnosticStatus.OK, label
    if fix_type >= warn_min:
        return DiagnosticStatus.WARN, label
    return DiagnosticStatus.ERROR, label


def apply_vertical_accuracy(level, message, v_acc, warn_m, error_m):
    """Fold the receiver's reported vertical accuracy into a classified status.

    fix_type is the receiver's opinion of its *solution*; v_acc is its opinion
    of the *result*, and the two can disagree. On 2026-08-20 this boat reported
    fix_type 6 -- 'RTK Fixed', OK, green tile -- alongside a vertical accuracy
    of 1.750 m. Tide and every sounding reduced through base_link carried that
    metre and a half, and nothing on the annunciator said so. Publishing v_acc
    as a key was half the fix; this is the other half.

    Raises the level, never lowers it: a receiver claiming 5 mm while holding a
    3D fix is still not an RTK fix, and this must not turn that WARN green.

    ``v_acc`` of ``None`` (not reported) passes straight through. Absent is not
    the same as good -- inventing an OK from a field the receiver never
    populated is exactly the mistake accuracy_text() exists to prevent, one
    level up.
    """
    if v_acc is None:
        return level, message
    if v_acc > error_m:
        worse = DiagnosticStatus.ERROR
    elif v_acc > warn_m:
        worse = DiagnosticStatus.WARN
    else:
        return level, message
    if level == DiagnosticStatus.STALE:
        # Stale data's accuracy describes whenever the feed died, not now.
        return level, message
    return max(level, worse), f'{message} - vertical {v_acc:.2f} m'


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
        # Reported vertical accuracy, in metres, at which the status is raised
        # regardless of fix_type. A working RTK fix on this hull reports 0.02
        # to 0.05 m; the 2026-08-20 failure reported 1.750 m while still
        # claiming fix_type 6. These bound what the tide chain can be trusted
        # to, so they are deliberately tighter than 'the receiver still has a
        # fix' -- 0.10 m is already worse than the 55 mm lever-arm error this
        # branch spent a day chasing, and 0.50 m is past any use for soundings.
        self.declare_parameter('warn_v_acc_m', 0.10)
        self.declare_parameter('error_v_acc_m', 0.50)
        # Hard-coded before, while stale_timeout was a parameter -- so a
        # sub-second timeout was unsatisfiable and nothing said so.
        self.declare_parameter('publish_rate', 1.0)

        self._topic = self.get_parameter('gps_raw_topic').value
        self._diagnostic_name = self.get_parameter('diagnostic_name').value
        self._hardware_id = self.get_parameter('hardware_id').value
        self._ok_min = self.get_parameter('ok_min_fix_type').value
        self._warn_min = self.get_parameter('warn_min_fix_type').value
        self._stale_timeout = self.get_parameter('stale_timeout').value
        self._warn_v_acc_m = self.get_parameter('warn_v_acc_m').value
        self._error_v_acc_m = self.get_parameter('error_v_acc_m').value
        rate = self.get_parameter('publish_rate').value
        if rate <= 0.0:
            raise ValueError(
                f'publish_rate must be positive, got {rate}. A diagnostics '
                'node that never publishes turns a fault into an absence.')
        publish_period = 1.0 / rate
        validate_thresholds(self._ok_min, self._warn_min)
        validate_stale_timeout(self._stale_timeout, publish_period)

        self._last_msg = None
        self._last_msg_time = None
        self._start_time = self.get_clock().now()

        self._pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self._sub = self.create_subscription(GPSRAW, self._topic, self._on_gps_raw, 10)
        self._timer = self.create_timer(publish_period, self._publish_diagnostic)

        self.get_logger().info(
            f'Publishing RTK diagnostics from "{self._topic}" as "{self._diagnostic_name}" '
            f'(OK >= {self._ok_min}, WARN >= {self._warn_min}; '
            f'vertical accuracy WARN > {self._warn_v_acc_m} m, '
            f'ERROR > {self._error_v_acc_m} m)'
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
            # publishing nothing -- but not on the first tick, ~1 s after
            # launch, before mavros has streamed anything: the tile flashed
            # red on every single boot, and an alarm that always cries wolf at
            # startup is one the operator learns to scroll past.
            waited = (now - self._start_time).nanoseconds / 1e9
            if 0.0 <= waited <= self._stale_timeout:
                status.level = DiagnosticStatus.WARN
                status.message = f'waiting for first message on "{self._topic}"'
            else:
                status.level = DiagnosticStatus.ERROR
                status.message = f'no data on "{self._topic}"'
            status.values = self._values(fix_type=-1, msg=None, age=None)
            self._publish(status, now)
            return

        msg = self._last_msg
        age = (now - self._last_msg_time).nanoseconds / 1e9
        if age < 0.0:
            # A backward clock step, routine on this GPS/NTP-disciplined boat
            # after boot. Unclamped it makes 'age > stale_timeout' false, so a
            # frozen fix_type reads fresh at exactly the moment the boat has
            # just come up.
            age = 0.0
            self.get_logger().warning(
                'clock stepped backward; treating the last GPSRAW as current')
        fix_type = msg.fix_type
        label = FIX_TYPE_LABELS.get(fix_type, f'Unknown ({fix_type})')

        if age > self._stale_timeout:
            # A frozen fix_type is worse than none: it reports the last good
            # state forever.
            status.level = DiagnosticStatus.STALE
            status.message = f'stale: no update for {age:.0f}s (last {label})'
        else:
            status.level, status.message = classify_fix(
                fix_type, self._ok_min, self._warn_min)

        status.level, status.message = apply_vertical_accuracy(
            status.level, status.message, accuracy_m(msg.v_acc),
            self._warn_v_acc_m, self._error_v_acc_m)

        status.values = self._values(fix_type, msg, age)
        self._publish(status, now)

    def _values(self, fix_type, msg, age):
        """The same key set on every path.

        The no-data branch used to carry gps_raw_topic and fix_type while every
        other path carried the accuracy and age keys and not gps_raw_topic, so
        anything reading the diagnostic had to treat 'key missing' and 'no
        data' as separate cases. Absent keys are how a fault reads as an
        absence, one level down from the status itself.
        """
        return [
            KeyValue(key='gps_raw_topic', value=str(self._topic)),
            KeyValue(key='fix_type', value=str(fix_type)),
            KeyValue(key='satellites_visible',
                     value='unknown' if msg is None
                     else satellite_text(msg.satellites_visible)),
            # eph/epv are DOP scaled by 100, with UINT16_MAX for unknown.
            KeyValue(key='hdop', value='unknown' if msg is None
                     else dop_text(msg.eph)),
            KeyValue(key='vdop', value='unknown' if msg is None
                     else dop_text(msg.epv)),
            # Vertical accuracy is the quantity tide and soundings depend on,
            # and it degrades long before fix_type does.
            KeyValue(key='h_acc_m', value='not reported' if msg is None
                     else accuracy_text(msg.h_acc)),
            KeyValue(key='v_acc_m', value='not reported' if msg is None
                     else accuracy_text(msg.v_acc)),
            KeyValue(key='age_s', value='-1.0' if age is None else f'{age:.1f}'),
        ]

    def _publish(self, status, now):
        array = DiagnosticArray()
        array.header.stamp = now.to_msg()
        array.status = [status]
        self._pub.publish(array)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        # Construction is inside the try for the same reason it is in
        # rtcm_diagnostics_node.py: a bad parameter -- an int launch override
        # against a float-typed threshold is enough -- raises here, and an
        # unhandled exception permanently silences /diagnostics. Absence reads
        # as health on the annunciator, which is the failure this whole file
        # exists to prevent, reintroduced one level up. Launch respawns this
        # node, so a clean exit that leaves rclpy shut down is what lets the
        # respawn mean anything.
        node = GpsRtkDiagnosticsNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
