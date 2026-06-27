#!/usr/bin/env python3
"""Unit tests for retrofit_m3_bag.py (#342).

Pure-logic tests (integer-second rounding, histogram, tf rewrite, path naming)
use lightweight fakes and need no ROS messages. Integration tests build a real
rosbag2 bag and round-trip it through main(); they request the `msgs` fixture,
which skips them if the message packages aren't on the path.

rosbag2's SequentialWriter always emits a *directory* bag (metadata.yaml +
<name>_0.mcap), even for a .mcap URI. Directory-bag round-trips use that form
directly; the bare-single-.mcap input form (boat bags) is built by extracting a
dir bag's inner segment and is covered by test_inplace_bare_mcap_stays_bare.
"""
import importlib.util
import os
import pathlib
import shutil
import types

import pytest

from rclpy.serialization import deserialize_message, serialize_message
from rosbag2_py import (ConverterOptions, SequentialReader, SequentialWriter,
                        StorageOptions, TopicMetadata)

# --- load the script as a module ------------------------------------------
HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE.parent / 'scripts' / 'retrofit_m3_bag.py'
_spec = importlib.util.spec_from_file_location('retrofit_m3_bag', SCRIPT)
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)

NS = rm.NS


# ======================================================================
# Pure-logic tests (no ROS messages)
# ======================================================================

def test_correct_stamp_healthy():
    """A ~0.04 s offset yields n=0, stamp unchanged, not ambiguous."""
    recv = 100 * NS
    stamp = recv + int(0.04 * NS)
    measured, applied, new_ns, ambiguous = rm.correct_stamp(stamp, recv)
    assert measured == 0
    assert applied == 0
    assert new_ns == stamp
    assert ambiguous is False


def test_correct_stamp_six_second_preserves_fraction():
    """A ~6.03 s offset removes 6 whole seconds, keeping the sub-second fraction."""
    recv = 100 * NS
    stamp = recv + int(6.03 * NS)
    measured, applied, new_ns, ambiguous = rm.correct_stamp(stamp, recv)
    assert measured == 6
    assert applied == 6
    assert new_ns == stamp - 6 * NS
    assert new_ns % NS == stamp % NS          # PPS-disciplined fraction untouched
    assert ambiguous is False


def test_correct_stamp_seven_second_step():
    """A later 7 s step is handled per-message (multi-step drift)."""
    recv = 200 * NS
    stamp = recv + int(7.02 * NS)
    measured, applied, new_ns, _ = rm.correct_stamp(stamp, recv)
    assert measured == 7
    assert applied == 7
    assert new_ns == stamp - 7 * NS


def test_correct_stamp_ambiguous_band():
    """A ~0.5 s offset lands in the ambiguous rounding band -> WARN flag."""
    recv = 100 * NS
    stamp = recv + int(0.5 * NS)
    measured, _applied, _new, ambiguous = rm.correct_stamp(stamp, recv)
    assert ambiguous is True
    assert measured == 0                       # round(0.5) -> 0 (banker's)


def test_correct_stamp_half_rounds_to_even():
    """Exactly n+0.5 rounds to even (round(2.5) -> 2) and flags ambiguous."""
    recv = 100 * NS
    stamp = recv + 2 * NS + NS // 2            # exactly +2.5 s
    measured, _applied, _new, ambiguous = rm.correct_stamp(stamp, recv)
    assert measured == 2
    assert ambiguous is True


def test_correct_stamp_forced_override_keeps_measured():
    """--offset forces the applied shift but the measured value is preserved."""
    recv = 100 * NS
    stamp = recv + int(6.03 * NS)
    measured, applied, new_ns, _ = rm.correct_stamp(stamp, recv, forced=7)
    assert measured == 6                       # histogram stays honest
    assert applied == 7
    assert new_ns == stamp - 7 * NS


def test_build_histogram():
    assert rm.build_histogram([0, 0, 6, 6, 6]) == {0: 2, 6: 3}
    assert rm.build_histogram([]) == {}


def _fake_tf(*child_frames):
    """Return a duck-typed TFMessage with the fields rewrite_tf touches."""
    transforms = []
    for cf in child_frames:
        transforms.append(types.SimpleNamespace(
            child_frame_id=cf,
            transform=types.SimpleNamespace(
                translation=types.SimpleNamespace(x=0.0, y=0.0, z=0.0))))
    return types.SimpleNamespace(transforms=transforms)


def test_rewrite_tf_target_frame():
    msg = _fake_tf('bizzy/m3')
    assert rm.rewrite_tf(msg) is True
    tr = msg.transforms[0].transform.translation
    assert (tr.x, tr.y, tr.z) == rm.M3_XYZ


def test_rewrite_tf_other_frame_untouched():
    msg = _fake_tf('bizzy/base_link')
    assert rm.rewrite_tf(msg) is False
    tr = msg.transforms[0].transform.translation
    assert (tr.x, tr.y, tr.z) == (0.0, 0.0, 0.0)


def test_rewrite_tf_idempotent():
    """Re-running sets the same value and still reports changed (field is set)."""
    msg = _fake_tf('bizzy/m3')
    rm.rewrite_tf(msg)
    assert rm.rewrite_tf(msg) is True
    tr = msg.transforms[0].transform.translation
    assert (tr.x, tr.y, tr.z) == rm.M3_XYZ


def test_detect_storage(tmp_path):
    bare = tmp_path / 'foo.mcap'
    bare.write_bytes(b'\x00')
    assert rm.detect_storage(str(bare)) == 'mcap'
    d = tmp_path / 'bagdir'
    d.mkdir()
    assert rm.detect_storage(str(d)) == ''


def test_inplace_paths_directory(tmp_path):
    d = tmp_path / 'bag'
    d.mkdir()
    temp, backup = rm.inplace_paths(str(d))
    assert temp == str(d) + '.tmp'
    assert backup == str(d) + '.orig'


def test_inplace_paths_bare_mcap(tmp_path):
    f = tmp_path / 'm3.mcap'
    f.write_bytes(b'\x00')
    temp, backup = rm.inplace_paths(str(f))
    assert temp == str(tmp_path / 'm3.tmp.mcap')
    assert backup == str(tmp_path / 'm3.orig.mcap')


# ======================================================================
# Integration tests (real rosbag2 bag round-trip)
# ======================================================================

@pytest.fixture
def msgs():
    """Message classes for fixtures; skip integration tests if unavailable."""
    geometry = pytest.importorskip('geometry_msgs.msg')
    tf2 = pytest.importorskip('tf2_msgs.msg')
    std = pytest.importorskip('std_msgs.msg')
    return geometry, tf2, std


def _topic_md(name, type_str):
    """Build a TopicMetadata for the installed rosbag2 (jazzy: id first positional)."""
    return TopicMetadata(0, name, type_str, 'cdr')


def _make_bag(path, msgs, *, detection_offsets, tf_old=True):
    """Write a synthetic M3 directory bag.

    detection_offsets: list of float seconds (header.stamp − receive_time) per ping.
    Writes the M3 detections topic (PointStamped — header carries the stamp), a
    /tf_static with a bizzy/m3 frame at the OLD offset + an unrelated frame, and a
    passthrough /chatter topic.
    """
    geometry, tf2, std = msgs
    wr = SequentialWriter()
    wr.open(StorageOptions(uri=str(path), storage_id='mcap'), ConverterOptions('', ''))
    wr.create_topic(_topic_md(rm.M3_DETECTIONS_TOPIC, 'geometry_msgs/msg/PointStamped'))
    wr.create_topic(_topic_md(rm.TF_STATIC_TOPIC, 'tf2_msgs/msg/TFMessage'))
    wr.create_topic(_topic_md('/chatter', 'std_msgs/msg/String'))

    recv0 = 1000 * NS
    for i, off in enumerate(detection_offsets):
        recv = recv0 + i * NS
        ps = geometry.PointStamped()
        stamp_ns = recv + int(round(off * NS))
        ps.header.stamp.sec = stamp_ns // NS
        ps.header.stamp.nanosec = stamp_ns % NS
        ps.header.frame_id = rm.M3_FRAME
        wr.write(rm.M3_DETECTIONS_TOPIC, serialize_message(ps), recv)

    tfm = tf2.TFMessage()
    t_m3 = geometry.TransformStamped()
    t_m3.header.frame_id = 'bizzy/base_link'
    t_m3.child_frame_id = rm.M3_FRAME
    if tf_old:
        t_m3.transform.translation.x = -0.23
        t_m3.transform.translation.z = -0.145
    t_other = geometry.TransformStamped()
    t_other.header.frame_id = 'bizzy/base_link'
    t_other.child_frame_id = 'bizzy/imu'
    t_other.transform.translation.x = 1.0
    tfm.transforms = [t_m3, t_other]
    wr.write(rm.TF_STATIC_TOPIC, serialize_message(tfm), recv0)

    s = std.String()
    s.data = 'hello'
    wr.write('/chatter', serialize_message(s), recv0)
    del wr


def _make_bare_mcap(tmp_path, msgs, name, **kw):
    """Build a genuine bare single .mcap file by extracting a dir bag's segment."""
    src = tmp_path / 'src'
    _make_bag(src, msgs, **kw)
    inner = [f for f in os.listdir(src) if f.endswith('.mcap')]
    assert len(inner) == 1
    bare = tmp_path / name
    shutil.move(str(src / inner[0]), str(bare))
    shutil.rmtree(src)
    return bare


def _read_all(path):
    """Return (storage_id, {topic: TopicMetadata}, [(topic, data, ts)])."""
    rd = SequentialReader()
    rd.open(StorageOptions(uri=str(path), storage_id=rm.detect_storage(str(path))),
            ConverterOptions('', ''))
    sid = rd.get_metadata().storage_identifier
    tmd = {t.name: t for t in rd.get_all_topics_and_types()}
    out = []
    while rd.has_next():
        out.append(rd.read_next())
    del rd
    return sid, tmd, out


def test_inplace_creates_backup_and_corrects(tmp_path, msgs):
    """Default mode: corrected bag at original name, original preserved as .orig."""
    bag = tmp_path / 'm3bag'
    _make_bag(bag, msgs, detection_offsets=[0.04, 6.03, 6.03])
    rc = rm.main([str(bag)])
    assert rc == 0
    assert (tmp_path / 'm3bag.orig').exists()
    assert bag.exists()

    geometry = msgs[0]
    _sid, _tmd, out = _read_all(bag)
    det = [m for m in out if m[0] == rm.M3_DETECTIONS_TOPIC]
    assert len(det) == 3
    for (_topic, data, ts) in det:
        ps = deserialize_message(data, geometry.PointStamped)
        stamp_ns = ps.header.stamp.sec * NS + ps.header.stamp.nanosec
        assert abs((stamp_ns - ts) / 1e9) < 0.5       # all realigned to ~receive time

    tf2 = msgs[1]
    tfm = [m for m in out if m[0] == rm.TF_STATIC_TOPIC][0]
    msg = deserialize_message(tfm[1], tf2.TFMessage)
    m3 = [t for t in msg.transforms if t.child_frame_id == rm.M3_FRAME][0]
    assert (m3.transform.translation.x, m3.transform.translation.y,
            m3.transform.translation.z) == rm.M3_XYZ
    other = [t for t in msg.transforms if t.child_frame_id == 'bizzy/imu'][0]
    assert other.transform.translation.x == 1.0       # unrelated frame untouched


def test_inplace_bare_mcap_stays_bare(tmp_path, msgs):
    """A bare single .mcap input yields a bare .mcap output (not a directory)."""
    bare = _make_bare_mcap(tmp_path, msgs, 'boat.mcap', detection_offsets=[6.03])
    assert bare.is_file()
    rc = rm.main([str(bare)])
    assert rc == 0
    assert (tmp_path / 'boat.mcap').is_file()          # still a bare FILE
    assert (tmp_path / 'boat.orig.mcap').is_file()     # backup is the original file
    geometry = msgs[0]
    _sid, _tmd, out = _read_all(tmp_path / 'boat.mcap')
    det = [m for m in out if m[0] == rm.M3_DETECTIONS_TOPIC]
    assert len(det) == 1
    ps = deserialize_message(det[0][1], geometry.PointStamped)
    stamp_ns = ps.header.stamp.sec * NS + ps.header.stamp.nanosec
    assert abs((stamp_ns - det[0][2]) / 1e9) < 0.5


def test_storage_and_metadata_preserved(tmp_path, msgs):
    """storage_id + every topic's TopicMetadata round-trip unchanged."""
    bag = tmp_path / 'm3bag'
    _make_bag(bag, msgs, detection_offsets=[6.03])
    in_sid, in_tmd, _ = _read_all(bag)
    rm.main([str(bag)])
    out_sid, out_tmd, _ = _read_all(bag)

    assert out_sid == in_sid
    assert set(out_tmd) == set(in_tmd)
    for name, md_in in in_tmd.items():
        md_out = out_tmd[name]
        assert md_out.type == md_in.type
        assert md_out.serialization_format == md_in.serialization_format
        assert md_out.offered_qos_profiles == md_in.offered_qos_profiles
        assert md_out.type_description_hash == md_in.type_description_hash


def test_out_mode_leaves_input_untouched(tmp_path, msgs):
    """--out writes a sibling and never modifies the input."""
    bag = tmp_path / 'm3bag'
    _make_bag(bag, msgs, detection_offsets=[6.03])
    _sid, _tmd, before = _read_all(bag)
    out = tmp_path / 'fixed'
    rm.main([str(bag), '--out', str(out)])
    assert out.exists()
    assert not (tmp_path / 'm3bag.orig').exists()
    _sid2, _tmd2, after = _read_all(bag)
    assert before == after                             # input unchanged


def test_passthrough_only(tmp_path, msgs):
    """--no-tf --no-timing: every message passes through byte-identical."""
    bag = tmp_path / 'm3bag'
    _make_bag(bag, msgs, detection_offsets=[6.03])
    _sid, _tmd, before = _read_all(bag)
    out = tmp_path / 'pass'
    rm.main([str(bag), '--out', str(out), '--no-tf', '--no-timing'])
    _sid2, _tmd2, after = _read_all(out)
    assert [(t, d) for (t, d, _) in before] == [(t, d) for (t, d, _) in after]


def test_report_only_exit_code_and_no_write(tmp_path, msgs):
    """--report-only writes nothing and exits 2 when corrections would apply."""
    bag = tmp_path / 'm3bag'
    _make_bag(bag, msgs, detection_offsets=[6.03])
    _sid, _tmd, before = _read_all(bag)
    rc = rm.main([str(bag), '--report-only'])
    assert rc == 2
    assert not (tmp_path / 'm3bag.orig').exists()
    _sid2, _tmd2, after = _read_all(bag)
    assert before == after                             # untouched


def test_report_only_clean_bag_exit_zero(tmp_path, msgs):
    """A healthy bag with no corrections -> report-only exits 0."""
    bag = tmp_path / 'm3bag'
    _make_bag(bag, msgs, detection_offsets=[0.04], tf_old=False)
    rc = rm.main([str(bag), '--report-only', '--no-tf'])
    assert rc == 0


def test_only_target_topic_timed(tmp_path, msgs):
    """Timing correction touches only M3_DETECTIONS_TOPIC, not other headers."""
    geometry, _tf2, _std = msgs
    bag = tmp_path / 'm3bag'
    wr = SequentialWriter()
    wr.open(StorageOptions(uri=str(bag), storage_id='mcap'), ConverterOptions('', ''))
    wr.create_topic(_topic_md('/other/stamped', 'geometry_msgs/msg/PointStamped'))
    recv = 1000 * NS
    ps = geometry.PointStamped()
    stamp_ns = recv + int(6.03 * NS)
    ps.header.stamp.sec = stamp_ns // NS
    ps.header.stamp.nanosec = stamp_ns % NS
    wr.write('/other/stamped', serialize_message(ps), recv)
    del wr

    out = tmp_path / 'fixed'
    rm.main([str(bag), '--out', str(out)])
    _sid, _tmd, msgs_out = _read_all(out)
    ps_out = deserialize_message(msgs_out[0][1], geometry.PointStamped)
    out_ns = ps_out.header.stamp.sec * NS + ps_out.header.stamp.nanosec
    assert out_ns == stamp_ns                          # unchanged (not the M3 topic)


def test_stale_temp_blocks_then_force_clears(tmp_path, msgs):
    """A leftover .tmp blocks an in-place run; --force clears it."""
    bag = tmp_path / 'm3bag'
    _make_bag(bag, msgs, detection_offsets=[6.03])
    stale = tmp_path / 'm3bag.tmp'
    stale.mkdir()
    (stale / 'junk').write_text('x')
    with pytest.raises(SystemExit):
        rm.main([str(bag)])
    assert stale.exists()                              # untouched without --force
    rc = rm.main([str(bag), '--force'])
    assert rc == 0
    assert (tmp_path / 'm3bag.orig').exists()
