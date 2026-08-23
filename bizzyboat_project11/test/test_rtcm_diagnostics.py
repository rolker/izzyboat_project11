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

from rclpy.time import Time

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


def test_an_x_y_swap_in_the_decoder_is_caught_by_the_captured_frame(monkeypatch):
    """Why the captured frame earns its place, demonstrated on the decoder.

    A frame this suite encoded itself cannot catch an axis swap: encode with
    the swap, decode with the swap, and the right answer comes back. A frame
    encoded outside this repo can. So swap the axes in the decoder for real --
    not in a separate expression alongside it -- and watch the captured frame's
    documented reference point stop matching: Washington DC lands in the
    western Pacific.
    """
    real_ecef_to_llh = rd.ecef_to_llh
    monkeypatch.setattr(rd, 'ecef_to_llh',
                        lambda x, y, z: real_ecef_to_llh(y, x, z))

    _, lat, lon, _ = rd.parse_reference_station(
        rd.iter_rtcm_frames(bytearray(CAPTURED_1005_FRAME))[0][0][1])

    assert abs(lon - CAPTURED_1005_LLH[1]) > 90.0
    # And the assertion the unswapped test makes would now fail, which is the
    # property being claimed.
    assert lon != pytest.approx(CAPTURED_1005_LLH[1], abs=1e-6)


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


@pytest.mark.parametrize('payload_len', [0, 1, 2, 3, 255, 256, 1023])
def test_the_whole_ten_bit_length_field_frames_correctly(payload_len):
    """The top 2 bits of the length live in the header's first byte, beside the
    reserved bits.

    Nothing here used to exceed 255 bytes, so those 2 bits were never
    exercised: widening RTCM_RESERVED_MASK from 0xFC to 0xFF passed the entire
    suite while silently discarding every frame longer than 255 bytes -- which
    is most of what an MSM7 mountpoint sends (1077/1087/1097/1127 routinely run
    past 700). 1023 is the longest a frame can declare.
    """
    stub = typed_payload(1077)
    payload = (stub + bytes(max(0, payload_len - len(stub))))[:payload_len]
    whole = frame(payload)
    assert len(whole) == payload_len + rd.RTCM_HEADER_LEN + rd.RTCM_CRC_LEN

    frames, consumed = rd.iter_rtcm_frames(bytearray(whole))

    assert consumed == len(whole)
    if payload_len >= 2:
        # Under 2 bytes there is no message number to report, so the frame is
        # validated and dropped rather than surfaced.
        assert [t for t, _ in frames] == [1077]
    else:
        assert frames == []


def test_a_maximum_length_frame_survives_leading_garbage():
    """The long-frame path and the resync path at once -- an MSM7 frame picked
    up mid-stream is the realistic case, and it is the one no test covered."""
    stub = typed_payload(1127)
    payload = stub + bytes(rd.RTCM_MAX_PAYLOAD - len(stub))
    buf = bytearray(b'\x00\xff\x12' + frame(payload))
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert [t for t, _ in frames] == [1127]
    assert consumed == len(buf)


# --- cost bound on hostile input -------------------------------------------

# Longest a single frame can be, and so the most the parser may legitimately
# hold back as a frame that might still be completed by the next delivery.
MAX_FRAME_LEN = rd.RTCM_HEADER_LEN + rd.RTCM_MAX_PAYLOAD + rd.RTCM_CRC_LEN


def crc_budget_for(buf):
    """The most CRC the parser may do in one call on ``buf``."""
    return rd.RTCM_CRC_BUDGET_FACTOR * len(buf) + rd.RTCM_MAX_FRAME


def counting_crc(monkeypatch):
    """Patch crc24q to record the length of every buffer it is asked to sum."""
    spans = []
    real = rd.crc24q

    def counted(data):
        spans.append(len(data))
        return real(data)

    monkeypatch.setattr(rd, 'crc24q', counted)
    return spans

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


# The pattern that defeats the reserved-bit filter: 0x03 leaves the reserved
# bits clear, so every third byte is a candidate header declaring the longest
# legal payload. Before the CRC budget this cost 1.10 s in a single _on_rtcm.
MAX_LENGTH_FALSE_HEADERS = b'\xd3\x03\xff'


@pytest.mark.parametrize('pattern', [
    MAX_LENGTH_FALSE_HEADERS,
    b'\xd3\x01\xff',         # 511-byte payloads: 1.21 s before the budget
    b'\xd3\x00',              # 1-byte payloads:   0.74 s before the budget
    b'\xd3',                   # rejected by the reserved bits alone
])
def test_no_input_can_exceed_the_crc_budget_in_one_call(pattern, monkeypatch):
    """The bound the reserved-bit filter does not provide.

    That filter is a filter: it drops 63 of every 64 false preambles, but a
    candidate declaring a maximum-length payload sails through it, so cost per
    callback was still unbounded by input. What bounds it is the budget -- and
    a budget is only a bound if nothing can talk the parser past it.
    """
    buf = bytearray((pattern * (rd.RTCM_MAX_BUFFER // len(pattern) + 1))
                    [:rd.RTCM_MAX_BUFFER])
    spans = counting_crc(monkeypatch)

    frames, consumed = rd.iter_rtcm_frames(buf)

    assert frames == []
    assert sum(spans) <= crc_budget_for(buf)
    # An absolute ceiling as well as the declared one, so that widening
    # RTCM_CRC_BUDGET_FACTOR cannot quietly widen the test with it. 4x the
    # buffer is ~20 ms of CRC; the 1 Hz timer survives that, and nothing a
    # conforming stream sends comes close to it.
    assert sum(spans) <= 4 * rd.RTCM_MAX_BUFFER
    # ...and the call still made progress, so a hostile stream cannot stall
    # the parser instead of wedging it.
    assert consumed > 0


def test_max_length_false_headers_cost_no_more_than_a_few_milliseconds():
    """Wall-clock backstop, measured against the 1.10 s this replaced."""
    import time
    buf = bytearray(MAX_LENGTH_FALSE_HEADERS
                    * (rd.RTCM_MAX_BUFFER // len(MAX_LENGTH_FALSE_HEADERS)))
    start = time.perf_counter()
    rd.iter_rtcm_frames(buf)
    assert time.perf_counter() - start < 0.10


def test_a_hostile_buffer_drains_and_gives_up_the_frame_hiding_behind_it():
    """Budget exhaustion must not lose the stream.

    The parser stops early on hostile input, so the caller sees it across
    several callbacks rather than one long one. Each must consume something,
    and a real frame sitting behind the garbage must still come out.
    """
    good = frame(station_1005(42, MACORS_42[0], MACORS_42[1], -10.3))
    garbage = MAX_LENGTH_FALSE_HEADERS * 400
    # Trailing filler so every false header in the garbage has room for the
    # frame it claims: this exercises budget exhaustion rather than the
    # separate "frame straddles the end of the buffer" path.
    buf = bytearray(garbage + good + bytes(MAX_FRAME_LEN))
    seen = []
    for _ in range(500):
        frames, consumed = rd.iter_rtcm_frames(buf)
        seen.extend(t for t, _ in frames)
        if consumed == 0:
            break
        del buf[:consumed]
        if not buf:
            break
    assert seen == [1005]


def test_the_budget_never_rejects_a_conforming_stream():
    """A budget that a real stream can exhaust would drop real corrections.

    Back-to-back maximum-length frames are the densest legal input there is,
    and they are exactly what an MSM7 mountpoint sends. One CRC pass each,
    well inside the budget.
    """
    stub = typed_payload(1077)
    payload = stub + bytes(rd.RTCM_MAX_PAYLOAD - len(stub))
    assert len(payload) == rd.RTCM_MAX_PAYLOAD
    whole = frame(payload)
    count = rd.RTCM_MAX_BUFFER // len(whole)
    buf = bytearray(whole * count)
    assert len(buf) <= rd.RTCM_MAX_BUFFER

    frames, consumed = rd.iter_rtcm_frames(buf)

    assert [t for t, _ in frames] == [1077] * count
    assert consumed == len(buf)


def test_alternating_garbage_that_survives_the_reserved_bits_is_still_bounded():
    """0xD3 0x00 pairs pass the reserved-bit check, so the CRC still runs.

    What stops it is the budget, not the filter, so the call now returns with
    bytes still in hand rather than grinding through the whole buffer -- the
    caller sees the same work spread over several callbacks.
    """
    buf = bytearray(b'\xd3\x00' * (rd.RTCM_MAX_BUFFER // 2))
    frames, consumed = rd.iter_rtcm_frames(buf)
    assert frames == []
    assert 0 < consumed <= len(buf)


def test_reserved_bits_set_on_an_otherwise_valid_frame_is_rejected():
    good = bytearray(frame(typed_payload(1074)))
    good[1] |= 0x04          # lowest reserved bit
    frames, _ = rd.iter_rtcm_frames(good)
    assert frames == []


# --- rover fix acceptance --------------------------------------------------

def test_a_good_fix_is_accepted():
    assert rd.fix_position_usable(0, BOAT[0], BOAT[1])
    assert rd.fix_position_usable(2, BOAT[0], BOAT[1])


def test_a_fix_with_no_solution_is_rejected():
    assert not rd.fix_position_usable(-1, BOAT[0], BOAT[1])


@pytest.mark.parametrize('lat,lon', [
    (float('nan'), -70.7115),
    (43.0720, float('nan')),
    (float('inf'), -70.7115),
    (43.0720, float('-inf')),
])
def test_a_non_finite_position_is_rejected(lat, lon):
    """nan was already rejected; inf was not, and inf reaches math.radians in
    the publish timer, where math.sin raises ValueError past main()'s
    KeyboardInterrupt-only guard. The process exits and /diagnostics goes
    silent -- which this node's own docstring says reads as health."""
    assert not rd.fix_position_usable(0, lat, lon)


@pytest.mark.parametrize('lat,lon', [
    (91.0, 0.0), (-90.001, 0.0), (0.0, 181.0), (0.0, -180.001), (1e30, 1e30),
])
def test_an_out_of_range_position_is_rejected(lat, lon):
    """Not a crash but a silent one: a nonsense latitude is a nonsense baseline
    and a confident ERROR about a station that is fine."""
    assert not rd.fix_position_usable(0, lat, lon)


def test_the_poles_and_the_antimeridian_are_still_valid_positions():
    for lat, lon in ((90.0, 180.0), (-90.0, -180.0)):
        assert rd.fix_position_usable(0, lat, lon)


def test_an_infinite_fix_never_reaches_the_baseline_maths():
    """The end-to-end statement of the same thing: whatever the guard is, an
    inf must not be able to reach math.sin."""
    assert not rd.fix_position_usable(0, float('inf'), 0.0)
    with pytest.raises(ValueError):
        rd.baseline_km(float('inf'), 0.0, MACORS_42[0], MACORS_42[1])


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


def test_zero_reference_point_is_rejected():
    """An unpopulated ARP decodes to latitude 90 and a height of -6357 km,
    which then reads as a 5218 km baseline -- a confident ERROR about a station
    that was never described."""
    w = BitWriter()
    w.u(1005, 12).u(3, 12).u(0, 6).u(0, 4)
    w.s(0, 38).u(0, 1).u(0, 1).s(0, 38).u(0, 2).s(0, 38)
    assert rd.parse_reference_station(w.bytes()) is None


def test_reference_point_far_off_the_ellipsoid_is_rejected():
    w = BitWriter()
    w.u(1005, 12).u(3, 12).u(0, 6).u(0, 4)
    w.s(round(1.0e6 * 1e4), 38).u(0, 1).u(0, 1)
    w.s(0, 38).u(0, 2).s(0, 38)
    assert rd.parse_reference_station(w.bytes()) is None


def test_real_reference_points_are_still_accepted():
    for lat, lon, height in ((MACORS_42[0], MACORS_42[1], -10.297),
                             (UDEL_649[0], UDEL_649[1], 68.0),
                             (0.0, 0.0, 0.0),
                             (-33.85, 151.21, 25.0)):
        assert rd.parse_reference_station(station_1005(1, lat, lon, height))


# --- message-type inventory decay ------------------------------------------

class FakeTypeInventory:
    """The node's message-type window without a ROS graph."""

    _recent_message_types = rd.RtcmDiagnosticsNode._recent_message_types
    _age = rd.RtcmDiagnosticsNode._age

    def __init__(self, window=60.0):
        self._message_type_window = window
        self._type_last_seen = {}

    def seen(self, message_type, seconds):
        self._type_last_seen[message_type] = Time(nanoseconds=int(seconds * 1e9))


def test_message_types_outside_the_window_drop_out():
    """After a mountpoint switch the old caster's types must not be merged with
    the new one's -- 'MSM4/5' from a boat receiving only one of them."""
    inventory = FakeTypeInventory(window=60.0)
    for message_type in (1075, 1085, 1095, 1125):     # the Delaware caster
        inventory.seen(message_type, 0.0)
    for message_type in (1074, 1084, 1094, 1124):     # MaCORS, 90 s later
        inventory.seen(message_type, 90.0)

    now = Time(nanoseconds=int(90.0 * 1e9))
    assert inventory._recent_message_types(now) == [1074, 1084, 1094, 1124]
    assert rd.summarise_msm(inventory._recent_message_types(now)) == \
        'MSM4 GPS+GLONASS+Galileo+BeiDou'


def test_message_types_inside_the_window_are_kept():
    inventory = FakeTypeInventory(window=60.0)
    inventory.seen(1074, 0.0)
    inventory.seen(1005, 30.0)
    now = Time(nanoseconds=int(50.0 * 1e9))
    assert inventory._recent_message_types(now) == [1005, 1074]


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

    def __init__(self, switch_m=1000.0, same_id_switch_m=50000.0):
        self._station = None
        self._first_station_position = None
        self._station_moved_m = 0.0
        self._station_reports = 0
        self._last_station_time = None
        self._station_switch_m = switch_m
        self._same_id_switch_m = same_id_switch_m
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
    """Two casters can serve the same station number; only the jump tells you.

    509 km is past same_id_switch_m, so this still resets -- unlike the routine
    VRS re-anchor below, which used to reset at 1 km and should not.
    """
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


# --- liveness: bytes are not frames ----------------------------------------

WARN_T, ERROR_T = 5.0, 15.0


def test_a_healthy_stream_is_ok():
    assert gd_liveness(1.0, 1.0)[0] == DiagnosticStatus.OK


def gd_liveness(byte_age, frame_age):
    return rd.classify_liveness(byte_age, frame_age, WARN_T, ERROR_T)


def test_no_bytes_at_all_is_an_error():
    assert gd_liveness(None, None)[0] == DiagnosticStatus.ERROR


def test_bytes_arriving_with_no_valid_frame_is_not_ok():
    """The gap this closes: _last_rtcm_time was stamped from raw byte arrival
    before framing, so a stream containing zero CRC-valid frames -- a half-open
    socket replaying a buffer, a mountpoint serving a format this cannot frame
    -- read 'OK - receiving corrections'."""
    level, message = gd_liveness(0.5, None)
    assert level == DiagnosticStatus.WARN
    assert 'no valid RTCM frame' in message


def test_a_stream_that_stops_framing_escalates_like_one_that_stops_arriving():
    assert gd_liveness(0.5, 8.0)[0] == DiagnosticStatus.WARN
    assert gd_liveness(0.5, 30.0)[0] == DiagnosticStatus.ERROR


def test_a_dead_stream_is_reported_as_dead_not_as_unframed():
    """Byte age dominates: 'no data for 30s' is more useful than 'no valid
    frame for 30s' when nothing is arriving at all."""
    level, message = gd_liveness(30.0, 30.0)
    assert level == DiagnosticStatus.ERROR
    assert message == 'no data for 30s'


# --- station identity vs a virtual station re-anchoring --------------------

SAME_ID_SWITCH_M = 50000.0


def test_a_different_station_id_resets_tracking():
    assert rd.should_reset_station_tracking(649, 42, 509000.0, SAME_ID_SWITCH_M)


def test_a_reused_station_number_at_another_caster_still_resets():
    """Two networks can serve the same station number; 509 km is the tell."""
    assert rd.should_reset_station_tracking(7, 7, 509000.0, SAME_ID_SWITCH_M)


def test_the_same_station_re_anchoring_does_not_reset_tracking():
    """A VRS is recomputed for the rover, so on a transit its reference point
    legitimately moves kilometres under one ID. Resetting threw away the very
    excursion history that identifies it as virtual, dropped the kind back to
    'unknown (single report)', and logged 'Reference station changed: 42 ->
    42'."""
    assert not rd.should_reset_station_tracking(42, 42, 4000.0, SAME_ID_SWITCH_M)


def test_a_small_move_under_one_id_still_does_not_reset():
    assert not rd.should_reset_station_tracking(42, 42, 3.0, SAME_ID_SWITCH_M)


def test_a_re_anchored_vrs_is_still_classified_virtual():
    """The consequence of not resetting: the excursion survives, so the kind
    is right."""
    assert rd.classify_station_kind(4000.0, 5, 5.0) == 'virtual (tracks rover)'


def test_a_vrs_re_anchoring_on_a_transit_keeps_its_history():
    """End to end through the node's own bookkeeping: the case that used to
    reset at 1 km and log 'Reference station changed: 42 -> 42'."""
    tracker = FakeStationTracker()
    tracker.record((42, MACORS_42[0], MACORS_42[1], -10.3))
    tracker.record((42, MACORS_42[0] + 0.02, MACORS_42[1], -10.3))   # ~2.2 km
    tracker.record((42, MACORS_42[0] + 0.04, MACORS_42[1], -10.3))
    assert tracker._station_reports == 3
    assert tracker._station_moved_m > 1000.0
    assert rd.classify_station_kind(tracker._station_moved_m,
                                    tracker._station_reports,
                                    5.0) == 'virtual (tracks rover)'
    assert not any('42 -> 42' in line for line in tracker.log)
