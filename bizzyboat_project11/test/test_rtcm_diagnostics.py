#!/usr/bin/env python3
"""Unit tests for rtcm_diagnostics_node.py.

All pure logic: RTCM3 framing and CRC, the 1005/1006 reference-point decode,
the ECEF->geodetic conversion, baseline distance, MSM summary, and the
threshold classification. No ROS graph is required.

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


# --- regressions on the two real casters -----------------------------------

BOAT = (43.0720, -70.7115)          # UNH pier, Portsmouth NH
UDEL_649 = (39.982667, -75.221965)  # decoded live 2026-08-21, Delaware caster
MACORS_42 = (42.862746, -70.890263)  # decoded live 2026-08-21 after the revert


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
