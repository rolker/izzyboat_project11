#!/usr/bin/env python3
"""Unit tests for rtcm_diagnostics_node.py.

All pure logic: RTCM3 framing and CRC, the 1005/1006 reference-point decode,
the ECEF->geodetic conversion, baseline distance, MSM summary, and the
threshold classification. No ROS graph is required.

Most cases build their own frames, which makes them self-consistent rather
than verified -- a bit-reversed CRC or a swapped X/Y would round-trip and pass.
The "external check vectors" section is the antidote: a catalogued CRC-24/LTE-A
check value and a complete 1005 frame encoded outside this repo, which pin the
implementation to something it did not produce itself.

The regression cases at the bottom are the two casters this boat has actually
been connected to -- the UDEL Delaware station found on 2026-08-21 at 509 km,
and the MassDOT MaCORS station it was moved back to at 27.4 km -- because those
are the numbers the diagnostic exists to distinguish.
"""
import importlib.util
import pathlib

import pytest

from diagnostic_msgs.msg import DiagnosticStatus

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'scripts' / 'rtcm_diagnostics_node.py'
_spec = importlib.util.spec_from_file_location('rtcm_diagnostics_node', SCRIPT)
rd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rd)


# --- helpers ---------------------------------------------------------------

class BitWriter:
    """Big-endian bit writer, the inverse of the node's _Bits reader."""

    def __init__(self):
        self.bits = []

    def u(self, value, count):
        for shift in range(count - 1, -1, -1):
            self.bits.append((value >> shift) & 1)
        return self

    def s(self, value, count):
        if value < 0:
            value += 1 << count
        return self.u(value, count)

    def bytes(self):
        while len(self.bits) % 8:
            self.bits.append(0)
        out = bytearray()
        for i in range(0, len(self.bits), 8):
            byte = 0
            for bit in self.bits[i:i + 8]:
                byte = (byte << 1) | bit
            out.append(byte)
        return bytes(out)


def frame(payload):
    """Wrap a payload in an RTCM3 frame with a valid CRC-24Q."""
    header = bytes([rd.RTCM_PREAMBLE, (len(payload) >> 8) & 0x03, len(payload) & 0xFF])
    crc = rd.crc24q(header + payload)
    return header + payload + bytes([(crc >> 16) & 0xFF, (crc >> 8) & 0xFF, crc & 0xFF])


def llh_to_ecef(lat_deg, lon_deg, height):
    import math
    e2 = rd.WGS84_F * (2.0 - rd.WGS84_F)
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    n = rd.WGS84_A / math.sqrt(1.0 - e2 * math.sin(lat) ** 2)
    return ((n + height) * math.cos(lat) * math.cos(lon),
            (n + height) * math.cos(lat) * math.sin(lon),
            (n * (1.0 - e2) + height) * math.sin(lat))


def station_1005(station_id, lat, lon, height):
    """Build a 1005 payload describing a station at the given position."""
    x, y, z = llh_to_ecef(lat, lon, height)
    w = BitWriter()
    w.u(1005, 12).u(station_id, 12).u(0, 6)
    w.u(1, 1).u(1, 1).u(1, 1).u(0, 1)
    w.s(round(x * 1e4), 38).u(0, 1).u(0, 1)
    w.s(round(y * 1e4), 38).u(0, 2)
    w.s(round(z * 1e4), 38)
    return w.bytes()


def typed_payload(message_type):
    """Smallest payload that carries a recognisable message number."""
    return BitWriter().u(message_type, 12).u(0, 12).bytes()


# --- the two real casters, used throughout ---------------------------------

BOAT = (43.0720, -70.7115)          # UNH pier, Portsmouth NH
UDEL_649 = (39.982667, -75.221965)  # decoded live 2026-08-21, Delaware caster
MACORS_42 = (42.862746, -70.890263)  # decoded live 2026-08-21 after the revert


# --- external check vectors ------------------------------------------------
#
# Everything else in this file builds its frames with BitWriter and its CRCs
# with the node's own crc24q, so the suite is self-consistent by construction:
# a bit-reversed CRC, or an X/Y swap in the decoder, would round-trip happily
# and every test would still pass. These two vectors come from outside this
# repo and are the only things here that can catch that.

# CRC-24/LTE-A: poly 0x1864CFB, init 0, no reflection, no final XOR -- the same
# parameters RTCM3 uses. Its catalogued check value is the CRC of the ASCII
# string "123456789".
CRC24_LTE_A_CHECK_INPUT = b'123456789'
CRC24_LTE_A_CHECK_VALUE = 0xCDE703

# A complete RTCM3 message-1005 frame, preamble to CRC, produced by an encoder
# outside this repo. Its three CRC bytes were computed elsewhere, so it
# validates here only if crc24q is bit-exact; and its antenna reference point
# decodes to a real place, so an X/Y swap or a sign error in the 38-bit ECEF
# fields cannot hide (see the swapped-axis test below).
CAPTURED_1005_FRAME = bytes.fromhex(
    'd300133ed7d3020298 0edeef34b4bd62ac09 41986f33360b98'.replace(' ', ''))
CAPTURED_1005_STATION_ID = 2003
CAPTURED_1005_ECEF = (1114104.5999, -4850729.7108, 3975521.4643)
CAPTURED_1005_LLH = (38.8047594, -77.0647736, 114.561)


def test_crc24q_matches_the_published_lte_a_check_value():
    """Pins the CRC to a catalogued vector, not to itself."""
    assert rd.crc24q(CRC24_LTE_A_CHECK_INPUT) == CRC24_LTE_A_CHECK_VALUE


def test_captured_frame_validates_against_its_own_crc():
    frames, consumed = rd.iter_rtcm_frames(bytearray(CAPTURED_1005_FRAME))
    assert [t for t, _ in frames] == [1005]
    assert consumed == len(CAPTURED_1005_FRAME)


def test_crc_over_a_frame_including_its_checksum_is_zero():
    """A property of CRC-24Q the captured frame lets us assert independently."""
    assert rd.crc24q(CAPTURED_1005_FRAME) == 0


def test_captured_frame_decodes_to_its_documented_reference_point():
    frames, _ = rd.iter_rtcm_frames(bytearray(CAPTURED_1005_FRAME))
    station_id, lat, lon, height = rd.parse_reference_station(frames[0][1])
    assert station_id == CAPTURED_1005_STATION_ID
    assert lat == pytest.approx(CAPTURED_1005_LLH[0], abs=1e-6)
    assert lon == pytest.approx(CAPTURED_1005_LLH[1], abs=1e-6)
    assert height == pytest.approx(CAPTURED_1005_LLH[2], abs=1e-3)


def test_captured_frame_ecef_round_trips_to_the_documented_metres():
    """Guards the geodetic conversion itself: back to ECEF, to the 0.1 mm the
    38-bit fields carry."""
    frames, _ = rd.iter_rtcm_frames(bytearray(CAPTURED_1005_FRAME))
    _, lat, lon, height = rd.parse_reference_station(frames[0][1])
    for got, want in zip(llh_to_ecef(lat, lon, height), CAPTURED_1005_ECEF):
        assert got == pytest.approx(want, abs=1e-3)


def test_swapping_x_and_y_would_be_caught():
    """Why the captured frame earns its place: the decoder's own encoder cannot
    catch an axis swap, but a real reference point can. Washington DC becomes
    the western Pacific."""
    _, lat, lon, _ = rd.parse_reference_station(
        rd.iter_rtcm_frames(bytearray(CAPTURED_1005_FRAME))[0][0][1])
    x, y, z = llh_to_ecef(lat, lon, 114.561)
    _, swapped_lon, _ = rd.ecef_to_llh(y, x, z)
    assert abs(swapped_lon - lon) > 90.0


# --- CRC -------------------------------------------------------------------

def test_crc24q_empty_is_zero():
    assert rd.crc24q(b'') == 0


def test_crc24q_is_stable_and_sensitive():
    a = rd.crc24q(b'\xd3\x00\x13')
    assert a == rd.crc24q(b'\xd3\x00\x13')
    assert a != rd.crc24q(b'\xd3\x00\x14')


def test_crc24q_in_range():
    assert 0 <= rd.crc24q(bytes(range(64))) <= 0xFFFFFF


# --- framing ---------------------------------------------------------------

def test_single_frame_round_trips():
    payload = typed_payload(1074)
    frames, consumed = rd.iter_rtcm_frames(bytearray(frame(payload)))
    assert [t for t, _ in frames] == [1074]
    assert consumed == len(frame(payload))


def test_multiple_frames_in_one_buffer():
    buf = bytearray(frame(typed_payload(1074)) + frame(typed_payload(1084))
                    + frame(typed_payload(1005)))
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert [t for t, _ in frames] == [1074, 1084, 1005]
    assert consumed == len(buf)


def test_partial_frame_is_left_for_next_call():
    whole = frame(typed_payload(1074))
    buf = bytearray(whole[:-2])
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert frames == []
    # Nothing consumed: the caller must keep the bytes and append more.
    assert consumed == 0
    buf.extend(whole[-2:])
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert [t for t, _ in frames] == [1074]
    assert consumed == len(whole)


def test_frame_split_across_two_deliveries_reassembles():
    """A message boundary mid-frame is the normal case on this transport."""
    whole = frame(station_1005(42, 42.86, -70.89, -10.3))
    buf = bytearray()
    for chunk in (whole[:7], whole[7:]):
        buf.extend(chunk)
        frames, consumed = rd.iter_rtcm_frames(buf)
        del buf[:consumed]
    assert [t for t, _ in frames] == [1005]


def test_corrupt_crc_is_rejected():
    bad = bytearray(frame(typed_payload(1074)))
    bad[-1] ^= 0xFF
    frames, _ = rd.iter_rtcm_frames(bad)
    assert frames == []


def test_resync_after_a_corrupt_frame_recovers_the_next_one():
    """The actual resync path: a damaged frame must not swallow the good one
    behind it. The parser steps one byte at a time until a header validates."""
    bad = bytearray(frame(typed_payload(1074)))
    bad[4] ^= 0xFF                    # corrupt the payload, so the CRC fails
    buf = bytearray(bad + frame(typed_payload(1084)))
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert [t for t, _ in frames] == [1084]
    assert consumed == len(buf)


def test_resync_from_a_mid_frame_start_recovers_the_next_frame():
    """Attaching to a stream already in progress: the first bytes are the tail
    of a frame whose header was never seen."""
    whole = frame(station_1005(42, MACORS_42[0], MACORS_42[1], -10.3))
    buf = bytearray(whole[5:] + frame(typed_payload(1074)))
    frames, _ = rd.iter_rtcm_frames(buf)
    assert [t for t, _ in frames] == [1074]


def test_false_preamble_inside_payload_does_not_desync():
    """0xD3 occurs in real payloads; only the CRC can tell us it is not a
    frame start."""
    payload = bytearray(typed_payload(1074))
    payload += b'\xd3\x00\x04garbage'
    buf = bytearray(frame(bytes(payload)) + frame(typed_payload(1084)))
    frames, _ = rd.iter_rtcm_frames(buf)
    assert [t for t, _ in frames] == [1074, 1084]


def test_pure_garbage_is_consumed_not_retained():
    buf = bytearray(b'\x01\x02\x03\x04')
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert frames == []
    assert consumed == len(buf)


def test_leading_garbage_before_a_good_frame():
    buf = bytearray(b'\x00\xff\x12' + frame(typed_payload(1005)))
    frames, _ = rd.iter_rtcm_frames(buf)
    assert [t for t, _ in frames] == [1005]


# --- cost bound on hostile input -------------------------------------------

# Longest a single frame can be, and so the most the parser may legitimately
# hold back as a frame that might still be completed by the next delivery.
MAX_FRAME_LEN = rd.RTCM_HEADER_LEN + rd.RTCM_MAX_PAYLOAD + rd.RTCM_CRC_LEN

def test_reserved_bits_reject_a_false_preamble_before_the_crc(monkeypatch):
    """The reserved-bit check is what keeps a garbled stream linear.

    A buffer of nothing but 0xD3 offers a candidate frame at every byte. Before
    the check, each was validated by CRC over ~979 bytes -- 3.4 s of CPU in one
    callback, measured on the boat's payload sizes, which starves the 1 Hz
    publish timer and takes /diagnostics silent. 0xD3 has reserved bits set
    (0xD3 & 0xFC = 0xD0), so not one CRC should now be computed.
    """
    calls = []
    real_crc = rd.crc24q
    monkeypatch.setattr(rd, 'crc24q', lambda data: calls.append(len(data)) or real_crc(data))

    buf = bytearray(b'\xd3' * rd.RTCM_MAX_BUFFER)
    frames, consumed = rd.iter_rtcm_frames(buf)

    assert frames == []
    assert calls == []
    # Only a possible straddling frame may be retained, never the whole buffer.
    assert len(buf) - consumed <= MAX_FRAME_LEN


def test_hostile_buffer_costs_no_more_than_a_few_milliseconds():
    """Wall-clock backstop on the same input, in case the check is ever moved.

    The bound is deliberately loose (100x under the 3.4 s that was measured):
    it is here to catch a return to quadratic behaviour, not to benchmark.
    """
    import time
    buf = bytearray(b'\xd3' * rd.RTCM_MAX_BUFFER)
    start = time.perf_counter()
    rd.iter_rtcm_frames(buf)
    assert time.perf_counter() - start < 0.03


def test_alternating_garbage_that_survives_the_reserved_bits_is_still_bounded():
    """0xD3 0x00 pairs pass the reserved-bit check, so the CRC still runs --
    but only once per candidate, and only over a declared length."""
    buf = bytearray(b'\xd3\x00' * (rd.RTCM_MAX_BUFFER // 2))
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert frames == []
    assert len(buf) - consumed <= MAX_FRAME_LEN


def test_reserved_bits_set_on_an_otherwise_valid_frame_is_rejected():
    good = bytearray(frame(typed_payload(1074)))
    good[1] |= 0x04          # lowest reserved bit
    frames, _ = rd.iter_rtcm_frames(good)
    assert frames == []


# --- reference station decode ---------------------------------------------

@pytest.mark.parametrize('lat,lon,height', [
    (42.862746, -70.890263, -10.297),
    (39.982667, -75.221965, 68.0),
    (0.0, 0.0, 0.0),
    (-33.85, 151.21, 25.0),
])
def test_station_position_round_trips(lat, lon, height):
    decoded = rd.parse_reference_station(station_1005(7, lat, lon, height))
    assert decoded is not None
    station_id, out_lat, out_lon, out_height = decoded
    assert station_id == 7
    assert out_lat == pytest.approx(lat, abs=1e-6)
    assert out_lon == pytest.approx(lon, abs=1e-6)
    assert out_height == pytest.approx(height, abs=1e-3)


def test_station_id_is_decoded():
    assert rd.parse_reference_station(station_1005(4095, 43.0, -70.0, 5.0))[0] == 4095


def test_non_station_message_returns_none():
    assert rd.parse_reference_station(typed_payload(1074)) is None


def test_short_payload_returns_none():
    assert rd.parse_reference_station(b'\x3e\x80') is None


def test_1006_is_accepted():
    payload = bytearray(station_1005(9, 43.0, -70.0, 5.0))
    # Rewrite the message number in place: 1006 shares 1005's leading fields.
    payload[0] = 1006 >> 4
    payload[1] = ((1006 & 0x0F) << 4) | (payload[1] & 0x0F)
    decoded = rd.parse_reference_station(bytes(payload))
    assert decoded is not None and decoded[0] == 9


# --- geodesy ---------------------------------------------------------------

def test_ecef_to_llh_on_the_equator():
    lat, lon, height = rd.ecef_to_llh(rd.WGS84_A, 0.0, 0.0)
    assert lat == pytest.approx(0.0, abs=1e-9)
    assert lon == pytest.approx(0.0, abs=1e-9)
    assert height == pytest.approx(0.0, abs=1e-6)


def test_ecef_to_llh_on_the_spin_axis_does_not_divide_by_zero():
    polar_b = rd.WGS84_A * (1.0 - rd.WGS84_F)
    lat, _, height = rd.ecef_to_llh(0.0, 0.0, polar_b)
    assert lat == pytest.approx(90.0, abs=1e-6)
    assert height == pytest.approx(0.0, abs=1e-6)


def test_baseline_zero_for_identical_points():
    assert rd.baseline_km(43.072, -70.7115, 43.072, -70.7115) == pytest.approx(0.0)


def test_baseline_one_degree_of_latitude():
    assert rd.baseline_km(43.0, -70.0, 44.0, -70.0) == pytest.approx(111.2, abs=0.5)


def test_baseline_is_symmetric():
    a = rd.baseline_km(43.072, -70.71, 39.98, -75.22)
    b = rd.baseline_km(39.98, -75.22, 43.072, -70.71)
    assert a == pytest.approx(b)


# --- MSM summary -----------------------------------------------------------

@pytest.mark.parametrize('message_type,expected', [
    (1074, ('GPS', 4)),
    (1077, ('GPS', 7)),
    (1084, ('GLONASS', 4)),
    (1094, ('Galileo', 4)),
    (1124, ('BeiDou', 4)),
    (1005, None),
    (1230, None),
])
def test_msm_info(message_type, expected):
    assert rd.msm_info(message_type) == expected


def test_summarise_msm_macors_shape():
    assert rd.summarise_msm({1074: 1, 1084: 1, 1094: 1, 1124: 1, 1006: 1}) == \
        'MSM4 GPS+GLONASS+Galileo+BeiDou'


def test_summarise_msm_delaware_shape():
    # The Delaware caster served MSM5 (1075 = GPS MSM5, not MSM7 -- MSM7 is
    # 1077). Getting this backwards in a field log is exactly why it is a test.
    assert rd.summarise_msm({1075: 1, 1085: 1, 1095: 1, 1125: 1, 1005: 1}) == \
        'MSM5 GPS+GLONASS+Galileo+BeiDou'


def test_summarise_msm_reports_mixed_levels():
    assert rd.summarise_msm({1074: 1, 1077: 1}) == 'MSM4/7 GPS'


def test_summarise_msm_without_msm_messages():
    assert rd.summarise_msm({1005: 1, 1230: 1}) == 'no MSM'


# --- threshold classification ---------------------------------------------

@pytest.mark.parametrize('distance,level', [
    (0.5, DiagnosticStatus.OK),
    (27.5, DiagnosticStatus.OK),      # MaCORS, the good case
    (35.0, DiagnosticStatus.OK),      # boundary is inclusive of OK
    (35.1, DiagnosticStatus.WARN),
    (99.9, DiagnosticStatus.WARN),
    (100.1, DiagnosticStatus.ERROR),
    (516.0, DiagnosticStatus.ERROR),  # Delaware, the case that hid for 18 days
])
def test_classify_baseline(distance, level):
    assert rd.classify_baseline(distance, 35.0, 100.0)[0] == level


def test_classify_baseline_message_only_set_when_degraded():
    assert rd.classify_baseline(10.0, 35.0, 100.0)[1] == ''
    assert 'degraded' in rd.classify_baseline(50.0, 35.0, 100.0)[1]
    assert 'not trustworthy' in rd.classify_baseline(500.0, 35.0, 100.0)[1]


# --- stale station description ---------------------------------------------

def test_staleness_does_not_mask_an_error_baseline():
    """The Delaware case with 1005/1006 stopped: still an ERROR.

    Returning early on staleness downgraded a 509 km base to WARN -- the exact
    condition the node exists to catch, hidden by a secondary one.
    """
    level, message = rd.apply_station_staleness(
        DiagnosticStatus.ERROR, 'station 649, 509.2 km', 120.0, 60.0)
    assert level == DiagnosticStatus.ERROR
    assert '120s ago' in message
    assert '509.2 km' in message


def test_staleness_raises_an_ok_baseline_to_warn():
    level, message = rd.apply_station_staleness(
        DiagnosticStatus.OK, 'station 42, 27.4 km', 90.0, 60.0)
    assert level == DiagnosticStatus.WARN
    assert '90s ago' in message


def test_fresh_station_description_is_left_alone():
    assert rd.apply_station_staleness(
        DiagnosticStatus.OK, 'station 42, 27.4 km', 5.0, 60.0) == \
        (DiagnosticStatus.OK, 'station 42, 27.4 km')


def test_never_described_station_is_left_alone():
    assert rd.apply_station_staleness(
        DiagnosticStatus.WARN, 'no fix', None, 60.0)[0] == DiagnosticStatus.WARN


# --- station kind and caster switches --------------------------------------

class FakeStationTracker:
    """The node's station bookkeeping without a ROS graph.

    _record_station is pure bookkeeping apart from the logger and the clock, so
    binding the real method to a stub tests the shipped code rather than a
    re-implementation of it.
    """

    def __init__(self, switch_m=1000.0):
        self._station = None
        self._first_station_position = None
        self._station_moved_m = 0.0
        self._station_reports = 0
        self._last_station_time = None
        self._station_switch_m = switch_m
        self.log = []

    def get_logger(self):
        tracker = self

        class _Logger:
            def info(self, message):
                tracker.log.append(message)
        return _Logger()

    def get_clock(self):
        class _Clock:
            def now(self):
                return 0
        return _Clock()

    _record_station = rd.RtcmDiagnosticsNode._record_station
    _reset_station_tracking = rd.RtcmDiagnosticsNode._reset_station_tracking

    def record(self, station):
        self._record_station(station)


def test_station_kind_needs_two_reports_before_asserting_physical():
    assert rd.classify_station_kind(0.0, 1, 5.0) == 'unknown (single report)'
    assert rd.classify_station_kind(0.0, 2, 5.0) == 'physical'


def test_station_kind_reports_virtual_once_the_point_walks():
    assert rd.classify_station_kind(120.0, 9, 5.0) == 'virtual (tracks rover)'


def test_physical_station_stays_physical_across_repeats():
    tracker = FakeStationTracker()
    for _ in range(5):
        tracker.record((42, MACORS_42[0], MACORS_42[1], -10.3))
    assert tracker._station_moved_m == pytest.approx(0.0, abs=1e-6)
    assert rd.classify_station_kind(tracker._station_moved_m,
                                    tracker._station_reports, 5.0) == 'physical'


def test_vrs_motion_is_detected():
    tracker = FakeStationTracker()
    for step in range(4):
        tracker.record((1, MACORS_42[0] + step * 0.001, MACORS_42[1], 0.0))
    assert tracker._station_moved_m > 5.0
    assert rd.classify_station_kind(tracker._station_moved_m,
                                    tracker._station_reports,
                                    5.0) == 'virtual (tracks rover)'


def test_caster_switch_does_not_latch_the_old_stations_excursion():
    """The 2026-08-21 revert: Delaware VRS, then MaCORS 509 km away.

    Before the reset, the 509 km jump was folded into the same running maximum
    and pinned reference_station_kind to 'virtual' for the process lifetime.
    """
    tracker = FakeStationTracker()
    for step in range(4):
        tracker.record((649, UDEL_649[0] + step * 0.001, UDEL_649[1], 68.0))
    assert rd.classify_station_kind(tracker._station_moved_m,
                                    tracker._station_reports,
                                    5.0) == 'virtual (tracks rover)'

    for _ in range(3):
        tracker.record((42, MACORS_42[0], MACORS_42[1], -10.3))
    assert tracker._station_moved_m == pytest.approx(0.0, abs=1e-6)
    assert rd.classify_station_kind(tracker._station_moved_m,
                                    tracker._station_reports, 5.0) == 'physical'
    assert any('649 -> 42' in line for line in tracker.log)


def test_same_id_at_a_wholly_different_position_also_resets():
    """Two casters can serve the same station number; the jump is the tell."""
    tracker = FakeStationTracker()
    tracker.record((7, UDEL_649[0], UDEL_649[1], 68.0))
    tracker.record((7, UDEL_649[0] + 0.001, UDEL_649[1], 68.0))
    tracker.record((7, MACORS_42[0], MACORS_42[1], -10.3))
    assert tracker._station_reports == 1
    assert tracker._station_moved_m == pytest.approx(0.0, abs=1e-6)


# --- rover fix expiry ------------------------------------------------------

def test_fresh_rover_fix_is_usable():
    assert rd.rover_fix_usable((43.07, -70.71), 0.4, 10.0)


def test_missing_rover_fix_is_not_usable():
    assert not rd.rover_fix_usable(None, None, 10.0)


def test_frozen_rover_fix_ages_out():
    """A fix that stopped updating during a transit would otherwise measure the
    baseline from where the boat used to be -- which can turn ERROR into OK."""
    assert not rd.rover_fix_usable((43.07, -70.71), 45.0, 10.0)


def test_rover_fix_at_the_timeout_boundary_is_still_usable():
    assert rd.rover_fix_usable((43.07, -70.71), 10.0, 10.0)


# --- regressions on the two real casters -----------------------------------



def test_delaware_caster_is_an_error():
    # 509.2 km by the WGS84 geodesic (pyproj Geod); the node's great-circle
    # approximation lands within 0.5 km of that, which is far finer than any
    # threshold cares about.
    distance = rd.baseline_km(BOAT[0], BOAT[1], UDEL_649[0], UDEL_649[1])
    assert distance == pytest.approx(509.2, abs=1.0)
    assert rd.classify_baseline(distance, 35.0, 100.0)[0] == DiagnosticStatus.ERROR


def test_macors_caster_is_ok():
    distance = rd.baseline_km(BOAT[0], BOAT[1], MACORS_42[0], MACORS_42[1])
    assert distance == pytest.approx(27.4, abs=0.5)
    assert rd.classify_baseline(distance, 35.0, 100.0)[0] == DiagnosticStatus.OK


def test_decoded_delaware_station_survives_a_frame_round_trip():
    """End to end: build the frame, parse it back, classify the baseline."""
    buf = bytearray(frame(station_1005(649, UDEL_649[0], UDEL_649[1], 68.0)))
    frames, _ = rd.iter_rtcm_frames(buf)
    station_id, lat, lon, height = rd.parse_reference_station(frames[0][1])
    assert station_id == 649
    assert height == pytest.approx(68.0, abs=1e-3)
    distance = rd.baseline_km(BOAT[0], BOAT[1], lat, lon)
    assert rd.classify_baseline(distance, 35.0, 100.0)[0] == DiagnosticStatus.ERROR
