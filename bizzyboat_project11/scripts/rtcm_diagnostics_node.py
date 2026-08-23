#!/usr/bin/env python3
"""Publish RTCM correction *provenance* as ROS diagnostics.

A liveness check ("bytes are arriving") cannot tell you whether the bytes are
any good. On 2026-08-21 this boat was found to have spent 18 days taking RTK
corrections from a caster 509 km away, left pointed at Delaware after the
Broadkill River deployment. Throughout, the NTRIP diagnostic read "OK -
receiving corrections" and the GPS RTK diagnostic read "OK - RTK Fixed",
because corrections *were* flowing and the receiver *was* reporting a fixed
solution. The solution was a false fix and the vertical wandered by metres.

This node answers the two questions those diagnostics cannot:

  * **Which** base station is correcting us (station ID and position, decoded
    from the RTCM 1005/1006 antenna-reference-point message)?
  * **How far away** is it (baseline distance to the current rover fix)?

Baseline length is the single best predictor of RTK quality: ionospheric and
tropospheric terms cancel between rover and base only while the two share an
atmosphere. Under ~35 km they largely do; past ~100 km ambiguity resolution is
not trustworthy no matter what fix flag the receiver raises.

It also publishes the liveness status the old ``ntrip_diagnostics_node.py``
published, under the same diagnostic name and with the same key names, so it is
a drop-in replacement rather than an addition.

Every status is published on every tick, including when no data has ever
arrived. A diagnostics node that goes silent when its input is missing turns a
fault into an absence, and absence reads as health.
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy)

from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from sensor_msgs.msg import NavSatFix

# WGS84
WGS84_A = 6378137.0
WGS84_F = 1.0 / 298.257223563
# Mean earth radius (IUGG), for great-circle baseline distance.
EARTH_MEAN_R_KM = 6371.0088

# RTCM3 framing
RTCM_PREAMBLE = 0xD3
RTCM_HEADER_LEN = 3
RTCM_CRC_LEN = 3
# The 6 bits between the preamble and the 10-bit length field are reserved and
# transmitted as zero. Checking them costs one AND and rejects 63 of every 64
# false preambles before the CRC is computed -- see iter_rtcm_frames.
RTCM_RESERVED_MASK = 0xFC
# Longest legal RTCM3 payload (10-bit length field).
RTCM_MAX_PAYLOAD = 1023
# The 10-bit length field lives in the low 2 bits of the first header byte and
# all 8 of the second.
RTCM_LENGTH_MASK = 0x03
# Longest a whole frame can be, preamble to CRC.
RTCM_MAX_FRAME = RTCM_HEADER_LEN + RTCM_MAX_PAYLOAD + RTCM_CRC_LEN
# Cap the reassembly buffer so a stream that never syncs cannot grow without
# bound. Four maximum-length frames is ample to recover framing after a
# dropped message.
RTCM_MAX_BUFFER = 4 * RTCM_MAX_FRAME
# How many bytes of CRC one call to iter_rtcm_frames may compute, as a multiple
# of the buffer it was given (plus one whole frame, so the head candidate is
# always affordable however small the buffer).
#
# The reserved-bit check below rejects 63 of every 64 false preambles for free,
# but it is a filter, not a bound: b"\xd3\x03\xff" repeated passes it and
# declares a 1023-byte payload, so every 3 bytes buys a 1026-byte CRC --
# measured at 1.10 s of CPU in a single _on_rtcm on one 4116-byte buffer, which
# starves the 1 Hz publish timer and takes /diagnostics silent. Only a budget
# bounds that, because no cheap test can tell a false header from a real one.
#
# A conforming stream never needs more than one CRC pass over each byte it
# delivered -- frames do not overlap, and a validated frame is skipped whole --
# so twice the buffer length cannot reject a real frame.
RTCM_CRC_BUDGET_FACTOR = 2

# A real antenna reference point sits within a few kilometres of the WGS84
# surface, so its ECEF norm is bounded. Zeros -- a placeholder ARP, or a
# 1005/1006 whose position fields were never filled in -- decode to latitude 90
# and a height of -6357 km, which then reads as a 5218 km baseline and a
# perfectly confident ERROR about a station that was never described.
ECEF_MIN_NORM_M = 6.3e6
ECEF_MAX_NORM_M = 6.5e6

# Station-description messages carrying the antenna reference point.
RTCM_STATIONARY_ARP = 1005
RTCM_STATIONARY_ARP_HEIGHT = 1006

# MSM message-number blocks, keyed by number // 10.
MSM_CONSTELLATIONS = {
    107: 'GPS',
    108: 'GLONASS',
    109: 'Galileo',
    110: 'SBAS',
    111: 'QZSS',
    112: 'BeiDou',
    113: 'NavIC',
}


def crc24q(data) -> int:
    """CRC-24Q over ``data``, the checksum RTCM3 frames carry.

    Validating it is what lets us treat a 0xD3 byte inside a payload as the
    coincidence it usually is, and resync cleanly after a dropped message.
    """
    crc = 0
    for byte in data:
        crc ^= byte << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


class _Bits:
    """Big-endian bit reader over a bytes-like payload."""

    def __init__(self, data):
        self._data = data
        self._pos = 0

    def u(self, count: int) -> int:
        value = 0
        for _ in range(count):
            byte = self._data[self._pos >> 3]
            value = (value << 1) | ((byte >> (7 - (self._pos & 7))) & 1)
            self._pos += 1
        return value

    def s(self, count: int) -> int:
        value = self.u(count)
        return value - (1 << count) if value & (1 << (count - 1)) else value


def iter_rtcm_frames(buf):
    """Extract complete, CRC-valid RTCM3 frames from ``buf``.

    Returns ``(frames, consumed)`` where ``frames`` is a list of
    ``(message_type, payload)`` and ``consumed`` is the number of leading bytes
    the caller should drop. Bytes belonging to a frame that is not yet complete
    are left in place for the next call.

    Cost is bounded on hostile input, which matters because a callback that
    runs for a second starves the 1 Hz publish timer and takes /diagnostics
    silent -- the node failing exactly the way it exists to prevent. Two
    mechanisms, and the second is the one that is load-bearing:

      * The reserved-bit check rejects a false preamble in constant time. It
        is what makes a buffer of nothing but 0xD3 (0xD3 & 0xFC = 0xD0, so
        every byte is rejected) cost 1.6 ms instead of the 3.4 s measured
        before it existed.
      * A CRC budget, because that check is a filter and not a bound: a
        candidate that declares a maximum-length payload passes it, and
        b"\xd3\x03\xff" repeated is 1.10 s of CRC in one callback. Once the
        budget is spent the scan stops and returns, consuming the bytes it has
        already proven cannot start a frame; the remainder is re-examined on
        the next call, with a fresh budget. Every call therefore costs at most
        RTCM_CRC_BUDGET_FACTOR * len(buf) + RTCM_MAX_FRAME bytes of CRC and
        consumes at least one byte, so no input can wedge the callback and
        none can stall the parser either.
    """
    frames = []
    index = 0
    # Enough for one whole frame however small the buffer, so the candidate at
    # the head of the buffer is always validated -- which is what guarantees
    # the forward progress described above.
    budget = RTCM_CRC_BUDGET_FACTOR * len(buf) + RTCM_MAX_FRAME
    while True:
        start = buf.find(RTCM_PREAMBLE, index)
        if start < 0:
            # No preamble anywhere: nothing here is recoverable.
            return frames, len(buf)
        if start + RTCM_HEADER_LEN > len(buf):
            return frames, start
        if buf[start + 1] & RTCM_RESERVED_MASK:
            # Reserved bits are non-zero, so this cannot be a frame header.
            # Reject before the CRC -- this is the cheap check that bounds the
            # cost of a garbled or hostile stream.
            index = start + 1
            continue
        # Masked explicitly rather than relying on the reserved-bit check above
        # having already forced the high 6 bits to zero: the two are separate
        # concerns, and a length read from unmasked bits would span megabytes.
        length = ((buf[start + 1] & RTCM_LENGTH_MASK) << 8) | buf[start + 2]
        end = start + RTCM_HEADER_LEN + length + RTCM_CRC_LEN
        if end > len(buf):
            # Frame straddles the end of the buffer; wait for more bytes.
            return frames, start
        span = end - start - RTCM_CRC_LEN
        if span > budget:
            # Out of CRC budget. Everything before this candidate has been
            # proven not to start a frame, so consume it and stop; the caller
            # keeps the rest and we resume here next call. start is never 0
            # at this point -- the budget always covers at least one whole
            # frame -- so this always makes progress.
            return frames, start
        budget -= span
        frame = bytes(buf[start:end])
        received = (frame[-3] << 16) | (frame[-2] << 8) | frame[-1]
        if crc24q(frame[:-RTCM_CRC_LEN]) != received:
            # False preamble (or corruption): step one byte and resync.
            index = start + 1
            continue
        payload = frame[RTCM_HEADER_LEN:RTCM_HEADER_LEN + length]
        if length >= 2:
            frames.append(((payload[0] << 4) | (payload[1] >> 4), payload))
        index = end


def parse_reference_station(payload):
    """Decode an RTCM 1005/1006 antenna reference point.

    Returns ``(station_id, latitude, longitude, height_m)``, or ``None`` if the
    payload is not a station-description message or is too short to hold one.
    """
    if len(payload) < 19:
        return None
    bits = _Bits(payload)
    message_type = bits.u(12)
    if message_type not in (RTCM_STATIONARY_ARP, RTCM_STATIONARY_ARP_HEIGHT):
        return None
    station_id = bits.u(12)
    bits.u(6)   # ITRF realisation year
    bits.u(1)   # GPS indicator
    bits.u(1)   # GLONASS indicator
    bits.u(1)   # Galileo indicator
    bits.u(1)   # reference-station indicator
    x = bits.s(38) * 1e-4
    bits.u(1)   # single receiver oscillator
    bits.u(1)   # reserved
    y = bits.s(38) * 1e-4
    bits.u(2)   # quarter-cycle indicator
    z = bits.s(38) * 1e-4
    if not ECEF_MIN_NORM_M <= math.sqrt(x * x + y * y + z * z) <= ECEF_MAX_NORM_M:
        # Not a point on the earth: a placeholder or unpopulated ARP. Better to
        # report the station as unknown than to invent a position for it.
        return None
    latitude, longitude, height = ecef_to_llh(x, y, z)
    return station_id, latitude, longitude, height


def ecef_to_llh(x, y, z):
    """Convert ECEF metres to WGS84 latitude/longitude (degrees) and height."""
    e2 = WGS84_F * (2.0 - WGS84_F)
    longitude = math.atan2(y, x)
    p = math.hypot(x, y)
    if p == 0.0:
        # On the spin axis: latitude is +/-90 and the iteration below divides
        # by cos(lat).
        latitude = math.copysign(math.pi / 2.0, z)
        height = abs(z) - WGS84_A * math.sqrt(1.0 - e2)
        return math.degrees(latitude), math.degrees(longitude), height
    latitude = math.atan2(z, p * (1.0 - e2))
    height = 0.0
    for _ in range(10):
        n = WGS84_A / math.sqrt(1.0 - e2 * math.sin(latitude) ** 2)
        height = p / math.cos(latitude) - n
        latitude = math.atan2(z, p * (1.0 - e2 * n / (n + height)))
    n = WGS84_A / math.sqrt(1.0 - e2 * math.sin(latitude) ** 2)
    height = p / math.cos(latitude) - n
    return math.degrees(latitude), math.degrees(longitude), height


def baseline_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km. Horizontal separation is what drives
    atmospheric decorrelation, so height is deliberately not included."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2.0) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2)
    return 2.0 * EARTH_MEAN_R_KM * math.asin(min(1.0, math.sqrt(a)))


def classify_baseline(distance_km, warn_km, error_km):
    """Map a baseline length to ``(diagnostic level, message suffix)``.

    Split out from the node so the thresholds that decide whether an RTK fix is
    believable are unit-testable without a ROS graph.
    """
    if distance_km > error_km:
        return DiagnosticStatus.ERROR, ' - fix not trustworthy'
    if distance_km > warn_km:
        return DiagnosticStatus.WARN, ' - degraded'
    return DiagnosticStatus.OK, ''


def apply_station_staleness(level, message, station_age, station_timeout):
    """Fold a stale station description into an already-classified status.

    A station that has stopped sending 1005/1006 is a WARN in its own right,
    but it must never *mask* the baseline classification. The last decoded
    position is still the base we are being corrected from: a 509 km base stays
    an ERROR whether or not it is still describing itself. Raising the level
    (rather than replacing it) is the whole point -- returning early on
    staleness downgraded exactly the condition this node was written to catch.
    """
    if station_age is None or station_age <= station_timeout:
        return level, message
    return (max(level, DiagnosticStatus.WARN),
            f'{message} (station last described {station_age:.0f}s ago)')


def classify_station_kind(moved_m, reports, motion_threshold_m):
    """Name what kind of base station the reference point describes.

    A virtual station is recomputed for the rover's position, so its reference
    point walks; a physical one does not move at all. One report cannot tell
    the two apart -- a VRS looks exactly like a physical station until it is
    seen a second time -- so say so rather than asserting 'physical' from a
    single observation.
    """
    if moved_m > motion_threshold_m:
        return 'virtual (tracks rover)'
    if reports < 2:
        return 'unknown (single report)'
    return 'physical'


def rover_fix_usable(fix, fix_age, fix_timeout):
    """Is the stored rover position still fit to compute a baseline from?

    A frozen fix is worse than no fix: the baseline is then measured from
    wherever the boat was when its position feed died, so a transit away from
    the base can turn ERROR back into OK while the boat drifts further from a
    base it can no longer see. Age it out and say so instead.
    """
    return fix is not None and fix_age is not None and fix_age <= fix_timeout


def msm_info(message_type):
    """Return ``(constellation, msm_level)`` for an MSM message, else None."""
    block, level = divmod(message_type, 10)
    if block in MSM_CONSTELLATIONS and 1 <= level <= 7:
        return MSM_CONSTELLATIONS[block], level
    return None


def summarise_msm(message_types):
    """Compact 'MSM4 GPS+GLONASS+Galileo+BeiDou' summary of a type inventory."""
    levels = set()
    constellations = []
    for message_type in sorted(message_types):
        info = msm_info(message_type)
        if info is None:
            continue
        constellation, level = info
        levels.add(level)
        if constellation not in constellations:
            constellations.append(constellation)
    if not constellations:
        return 'no MSM'
    level_text = ('MSM' + '/'.join(str(level) for level in sorted(levels)))
    return f'{level_text} {"+".join(constellations)}'


class RtcmDiagnosticsNode(Node):

    def __init__(self):
        super().__init__('rtcm_diagnostics')

        self.declare_parameter('rtcm_topic', 'mavros/gps_rtk/send_rtcm')
        # 'mavros_msgs' (RTCM.data) or 'rtcm_msgs' (Message.message).
        self.declare_parameter('rtcm_message_package', 'mavros_msgs')
        self.declare_parameter('fix_topic', 'mavros/global_position/global')
        self.declare_parameter('liveness_diagnostic_name', 'NTRIP')
        self.declare_parameter('provenance_diagnostic_name', 'RTK: corrections')
        self.declare_parameter('hardware_id', '')
        # Seconds without RTCM before WARN / ERROR.
        self.declare_parameter('warn_timeout', 5.0)
        self.declare_parameter('error_timeout', 15.0)
        # Baseline thresholds. Under ~35 km the atmosphere largely cancels;
        # past ~100 km a reported fix should not be believed.
        self.declare_parameter('warn_baseline_km', 35.0)
        self.declare_parameter('error_baseline_km', 100.0)
        # 1005/1006 are typically sent every 5-10 s; allow generous slack
        # before declaring the station identity unknown.
        self.declare_parameter('station_timeout', 60.0)
        # The rover fix arrives at ~10 Hz. Ten seconds without one means the
        # position feed is gone, and a baseline computed from the last one is
        # measured from wherever the boat was when it stopped.
        self.declare_parameter('fix_timeout', 10.0)
        # A reference point that walks further than this from where it was
        # first seen is a virtual station being recomputed for our position,
        # not a real one.
        self.declare_parameter('vrs_motion_threshold_m', 5.0)
        # A reference point that JUMPS further than this between consecutive
        # reports is a different base station -- a caster or mountpoint switch,
        # as on 2026-08-21 -- not a VRS tracking us. A VRS walks with the boat,
        # so metres per report; a switch is the whole baseline at once.
        self.declare_parameter('station_switch_m', 1000.0)
        self.declare_parameter('publish_rate', 1.0)
        # Recent-history window for the message-type inventory. Counts that
        # never decay merge two casters into one after a mountpoint switch --
        # 'MSM4/5' from a boat that only ever received one of them.
        self.declare_parameter('message_type_window', 60.0)
        # Caster identity, for the record. These names line up with the NTRIP
        # credentials YAML so the same file can be passed to this node; the
        # password in that file is deliberately never declared or read.
        self.declare_parameter('host', '')
        self.declare_parameter('port', 0)
        self.declare_parameter('mountpoint', '')

        self._rtcm_topic = self.get_parameter('rtcm_topic').value
        self._fix_topic = self.get_parameter('fix_topic').value
        self._liveness_name = self.get_parameter('liveness_diagnostic_name').value
        self._provenance_name = self.get_parameter('provenance_diagnostic_name').value
        self._hardware_id = self.get_parameter('hardware_id').value
        self._warn_timeout = self.get_parameter('warn_timeout').value
        self._error_timeout = self.get_parameter('error_timeout').value
        self._warn_baseline_km = self.get_parameter('warn_baseline_km').value
        self._error_baseline_km = self.get_parameter('error_baseline_km').value
        self._station_timeout = self.get_parameter('station_timeout').value
        self._fix_timeout = self.get_parameter('fix_timeout').value
        self._vrs_motion_threshold_m = self.get_parameter('vrs_motion_threshold_m').value
        self._station_switch_m = self.get_parameter('station_switch_m').value
        self._message_type_window = self.get_parameter('message_type_window').value
        rate = self.get_parameter('publish_rate').value
        if rate <= 0.0:
            raise ValueError(
                f'publish_rate must be positive, got {rate}. A diagnostics node '
                'that never publishes turns a fault into an absence.')

        self._buffer = bytearray()
        self._message_count = 0
        self._byte_count = 0
        self._last_rtcm_time = None
        self._last_station_time = None
        self._station = None
        self._first_station_position = None
        self._station_moved_m = 0.0
        self._station_reports = 0
        self._message_types = {}
        self._type_last_seen = {}
        self._rover_fix = None
        self._last_fix_time = None

        # BEST_EFFORT subscriptions are compatible with both BEST_EFFORT and
        # RELIABLE publishers, so this node attaches to whatever the NTRIP
        # client and mavros happen to offer. A dropped sample costs at most a
        # resync, which the CRC check handles.
        qos = QoSProfile(depth=50, history=HistoryPolicy.KEEP_LAST,
                         reliability=ReliabilityPolicy.BEST_EFFORT,
                         durability=DurabilityPolicy.VOLATILE)

        package = self.get_parameter('rtcm_message_package').value
        if package == 'rtcm_msgs':
            from rtcm_msgs.msg import Message as RtcmMessage
            self._payload_field = 'message'
        elif package == 'mavros_msgs':
            from mavros_msgs.msg import RTCM as RtcmMessage
            self._payload_field = 'data'
        else:
            # Falling through to mavros_msgs on a typo subscribes to a topic
            # that never matches, and the node then reports 'no corrections'
            # forever while corrections are in fact flowing.
            raise ValueError(
                f'rtcm_message_package must be "mavros_msgs" or "rtcm_msgs", '
                f'got "{package}"')

        # The NTRIP credentials YAML is passed to this node whole so the caster
        # actually in force appears in the diagnostic. The password is safe only
        # because an undeclared parameter is dropped, so assert that rather than
        # trusting it: if this node ever gains undeclared-parameter support, the
        # secret would land in a diagnostic published to the whole fleet.
        for name in ('password', 'passwd', 'secret', 'token', 'ntrip_password'):
            if self.has_parameter(name):
                raise ValueError(
                    f'refusing to run: parameter "{name}" is declared on a node '
                    'that publishes its parameters in a diagnostic')

        self._pub = self.create_publisher(DiagnosticArray, '/diagnostics', 10)
        self._rtcm_sub = self.create_subscription(
            RtcmMessage, self._rtcm_topic, self._on_rtcm, qos)
        self._fix_sub = self.create_subscription(
            NavSatFix, self._fix_topic, self._on_fix, qos)
        self._timer = self.create_timer(1.0 / rate, self._publish_diagnostics)

        self.get_logger().info(
            f'Monitoring RTCM provenance on "{self._rtcm_topic}" '
            f'({package}) against "{self._fix_topic}"; '
            f'baseline WARN > {self._warn_baseline_km} km, '
            f'ERROR > {self._error_baseline_km} km'
        )

    # -- inputs ------------------------------------------------------------

    def _on_rtcm(self, msg):
        payload = bytes(getattr(msg, self._payload_field))
        self._last_rtcm_time = self.get_clock().now()
        self._message_count += 1
        self._byte_count += len(payload)

        self._buffer.extend(payload)
        if len(self._buffer) > RTCM_MAX_BUFFER:
            del self._buffer[:-RTCM_MAX_BUFFER]

        frames, consumed = iter_rtcm_frames(self._buffer)
        del self._buffer[:consumed]
        for message_type, frame_payload in frames:
            self._message_types[message_type] = \
                self._message_types.get(message_type, 0) + 1
            self._type_last_seen[message_type] = self._last_rtcm_time
            station = parse_reference_station(frame_payload)
            if station is not None:
                self._record_station(station)

    def _record_station(self, station):
        station_id, latitude, longitude, _ = station

        if self._station is not None:
            previous_id, previous_lat, previous_lon, _ = self._station
            jump_m = 1000.0 * baseline_km(previous_lat, previous_lon,
                                          latitude, longitude)
            if previous_id != station_id or jump_m > self._station_switch_m:
                # A different base station. Without this reset the excursion
                # accumulated from the OLD station's position pins
                # reference_station_kind to 'virtual' for the life of the
                # process -- which is exactly what a Delaware-to-MaCORS revert
                # looks like, and it must not poison the new station's
                # classification.
                self.get_logger().info(
                    f'Reference station changed: {previous_id} -> {station_id}, '
                    f'{jump_m / 1000.0:.1f} km away; restarting motion tracking')
                self._reset_station_tracking()

        self._station_reports += 1
        if self._first_station_position is None:
            self._first_station_position = (latitude, longitude)
        else:
            moved_m = 1000.0 * baseline_km(
                self._first_station_position[0], self._first_station_position[1],
                latitude, longitude)
            self._station_moved_m = max(self._station_moved_m, moved_m)
        self._station = station
        self._last_station_time = self.get_clock().now()

    def _reset_station_tracking(self):
        self._first_station_position = None
        self._station_moved_m = 0.0
        self._station_reports = 0

    def _on_fix(self, msg: NavSatFix):
        if msg.status.status >= 0 and not (math.isnan(msg.latitude)
                                           or math.isnan(msg.longitude)):
            self._rover_fix = (msg.latitude, msg.longitude)
            self._last_fix_time = self.get_clock().now()

    # -- outputs -----------------------------------------------------------

    def _recent_message_types(self, now):
        """Message types seen within the decay window.

        Cumulative counts describe the whole session, which after a mountpoint
        switch is two casters at once: the inventory would claim MSM4/5 from
        both when only one is being received. What the operator needs is what
        is arriving NOW.
        """
        return sorted(
            message_type for message_type, stamp in self._type_last_seen.items()
            if (self._age(stamp, now) or 0.0) <= self._message_type_window)

    def _age(self, stamp, now):
        if stamp is None:
            return None
        return (now - stamp).nanoseconds / 1e9

    def _liveness_status(self, now):
        status = DiagnosticStatus()
        status.name = self._liveness_name
        status.hardware_id = self._hardware_id
        age = self._age(self._last_rtcm_time, now)

        if age is None:
            status.level = DiagnosticStatus.ERROR
            status.message = 'no data received'
            age_text = '-1.0'
        else:
            age_text = f'{age:.1f}'
            if age > self._error_timeout:
                status.level = DiagnosticStatus.ERROR
                status.message = f'no data for {age:.0f}s'
            elif age > self._warn_timeout:
                status.level = DiagnosticStatus.WARN
                status.message = f'no data for {age:.0f}s'
            else:
                status.level = DiagnosticStatus.OK
                status.message = 'receiving corrections'

        status.values = [
            # Key names kept identical to the retired ntrip_diagnostics_node so
            # this is a drop-in replacement for anything already reading them.
            KeyValue(key='messages_received', value=str(self._message_count)),
            KeyValue(key='last_rtcm_age_s', value=age_text),
            KeyValue(key='bytes_received', value=str(self._byte_count)),
            KeyValue(key='rtcm_topic', value=str(self._rtcm_topic)),
        ]
        return status

    def _provenance_status(self, now):
        status = DiagnosticStatus()
        status.name = self._provenance_name
        status.hardware_id = self._hardware_id

        station_age = self._age(self._last_station_time, now)
        fix_age = self._age(self._last_fix_time, now)
        recent_types = self._recent_message_types(now)
        types_text = '+'.join(str(t) for t in recent_types)
        values = [
            KeyValue(key='caster_host', value=str(self.get_parameter('host').value)),
            KeyValue(key='caster_port', value=str(self.get_parameter('port').value)),
            KeyValue(key='caster_mountpoint',
                     value=str(self.get_parameter('mountpoint').value)),
            KeyValue(key='message_types', value=types_text or 'none'),
            KeyValue(key='msm', value=summarise_msm(recent_types)),
            # Published unconditionally: a baseline is only as current as the
            # rover position it was measured from, and that age was previously
            # invisible to anyone reading the diagnostic.
            KeyValue(key='rover_fix_age_s',
                     value='-1.0' if fix_age is None else f'{fix_age:.1f}'),
        ]

        if self._station is None:
            # Corrections may well be flowing; we simply cannot say from where,
            # which is exactly the condition that hid the Delaware caster.
            status.level = (DiagnosticStatus.ERROR if self._last_rtcm_time is None
                            else DiagnosticStatus.WARN)
            status.message = ('no corrections' if self._last_rtcm_time is None
                              else 'station unknown (no 1005/1006 yet)')
            status.values = values
            return status

        station_id, latitude, longitude, height = self._station
        kind = classify_station_kind(self._station_moved_m,
                                     self._station_reports,
                                     self._vrs_motion_threshold_m)
        values.extend([
            KeyValue(key='reference_station_id', value=str(station_id)),
            KeyValue(key='reference_latitude', value=f'{latitude:.7f}'),
            KeyValue(key='reference_longitude', value=f'{longitude:.7f}'),
            KeyValue(key='reference_height_m', value=f'{height:.3f}'),
            KeyValue(key='reference_station_kind', value=kind),
            KeyValue(key='reference_moved_m', value=f'{self._station_moved_m:.1f}'),
            KeyValue(key='last_station_msg_age_s',
                     value='-1.0' if station_age is None else f'{station_age:.1f}'),
        ])

        if not rover_fix_usable(self._rover_fix, fix_age, self._fix_timeout):
            reason = ('no fix' if self._rover_fix is None
                      else f'rover fix {fix_age:.0f}s old')
            status.level = DiagnosticStatus.WARN
            status.message = f'station {station_id}, baseline unknown ({reason})'
            values.append(KeyValue(key='baseline_km', value='nan'))
        else:
            distance = baseline_km(self._rover_fix[0], self._rover_fix[1],
                                   latitude, longitude)
            values.append(KeyValue(key='baseline_km', value=f'{distance:.1f}'))
            status.level, detail = classify_baseline(
                distance, self._warn_baseline_km, self._error_baseline_km)
            status.message = (f'station {station_id}, {distance:.1f} km, '
                              f'{summarise_msm(recent_types)}{detail}')

        status.level, status.message = apply_station_staleness(
            status.level, status.message, station_age, self._station_timeout)
        status.values = values
        return status

    def _publish_diagnostics(self):
        now = self.get_clock().now()
        array = DiagnosticArray()
        array.header.stamp = now.to_msg()
        array.status = [self._liveness_status(now), self._provenance_status(now)]
        self._pub.publish(array)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        # Construction is inside the try: a bad parameter raises here, and
        # leaving rclpy initialised on the way out is how a launch-time
        # configuration error becomes a hung process rather than a clean exit.
        node = RtcmDiagnosticsNode()
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
