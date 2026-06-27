#!/usr/bin/env python3
"""Retrofit a collected bizzy M3 (Kongsberg) bag with corrected geometry + timing.

ONE-OFF utility. New captures should not need this once the boat's clock-sync is
fixed (#338) and the corrected M3 transducer offset is in the URDF (#339/#341).
This exists to make *already-recorded* M3 bags reprocessable (cube_bathymetry
import) with correct georeferencing. Run it manually; it is not a ROS node and is
not installed.

Two independent corrections, each toggleable:

  * /tf_static  ->  the `bizzy/m3` transducer transform's TRANSLATION is set to
    the measured (-0.29, 0.0, -0.28). Rotation is left untouched (only the
    offsets changed in #339; the M3 orientation is still pending a patch test).
    The old recorded value (-0.23, 0.0, -0.145) put the transducer face ~13.5 cm
    too shallow -> a constant sounding-depth bias. Idempotent: re-running sets
    the same value. Applies to every M3 bag (the offset was wrong since install).

  * /bizzy/sensors/m3/detections  ->  the detection header.stamp is corrected for
    the integer-second clock skew (#338). From Jun 24 2026 the M3's absolute
    time-of-day jumped ahead in WHOLE-second steps (a drifting mercat Windows
    clock) while PPS kept the sub-second fraction correct. So the fix is an
    INTEGER-second shift that PRESERVES the sub-second fraction:

        n = round(header.stamp - bag_receive_time)   # nearest whole second
        header.stamp -= n seconds                     # fraction untouched

    This is computed PER MESSAGE against the bag's receive timestamp (the gabby
    clock, which #338 confirms agreed with every other clock to < 2 ms). Doing it
    per-message means a bag that straddles a 6 s -> 7 s jump gets each ping
    corrected by its own integer, and a healthy ping (offset ~0.04 s -> n = 0) is
    left untouched. The bag receive time only needs ±0.5 s accuracy to pick the
    right integer; healthy (~0.04 s) and bad (~6.03 s) offsets are both far from a
    0.5 s rounding boundary. A WARN is emitted for any ping whose fractional
    offset lands in an ambiguous band (|frac| in [0.3, 0.7]).

The integer-offset HISTOGRAM is always printed (e.g. "0 s: 412, 6 s: 1805") so
the step structure is visible and the PPS assumption is validated. Use
--report-only to see it without writing (exits non-zero if any correction would
apply, so it doubles as a "does this bag need fixing?" probe in batch scripts).

File handling (default: in-place with backup) — downstream paths reference the
original bag name, so the corrected bag takes the original name and the original
is preserved as a backup. Persist-then-rename: the corrected bag is written to a
temp path and VALIDATED (open + read one message) BEFORE the original is renamed
to `<name>.orig` and the temp moved into place, so a failed/partial write never
destroys the original. `--out PATH` instead writes a non-destructive sibling
(the retrofit_sidescan_bag.py style) and never touches the input.

Offline read/write (rosbag2), no replay. Requires a sourced ROS 2 (jazzy) env.
Storage format + QoS are preserved (writer reuses the reader's TopicMetadata).

NOTE on bare .mcap: boat bags are often bare single `.mcap` files (not rosbag2
directories). This script detects the input form and opens bare files with
storage_id='mcap'. rosbag2's writer may emit a *directory* bag for mcap output
even from a bare-file input; the result is still correct and reloadable, but
smoke-test the bare-file round-trip on a real boat bag before bulk use.

Usage:
    python3 retrofit_m3_bag.py <in_bag> [--out OUT] [--report-only] \
        [--offset N] [--no-tf] [--no-timing]

See #342 / #338 / #339, and retrofit_sidescan_bag.py (the precedent).
"""
import argparse
import os
import shutil
import sys

from rclpy.serialization import deserialize_message, serialize_message
from rosbag2_py import (ConverterOptions, SequentialReader, SequentialWriter,
                        StorageOptions)
from rosidl_runtime_py.utilities import get_message

NS = 1_000_000_000

# Timing-correction target (must-fix, Plan Review): the M3 detections topic, from
# the recorder config in bizzyboat.yaml. Type marine_acoustic_msgs/SonarDetections.
# A namespace/topic rename is a one-line change here.
M3_DETECTIONS_TOPIC = '/bizzy/sensors/m3/detections'

# Geometry-correction target.
TF_STATIC_TOPIC = '/tf_static'
M3_FRAME = 'bizzy/m3'
M3_XYZ = (-0.29, 0.0, -0.28)   # measured 2026-06-27 (#339); supersedes (-0.23,0,-0.145)

# Fractional offset band (seconds either side of a half-second) that makes the
# round-to-nearest-second ambiguous; pings here get a WARN.
AMBIG_LO, AMBIG_HI = 0.3, 0.7


def correct_stamp(stamp_ns, recv_ns, forced=None):
    """Integer-second stamp correction, preserving the sub-second fraction.

    Returns (n, new_stamp_ns, ambiguous): the whole-second shift applied, the
    corrected stamp in ns, and whether the raw fractional offset was in the
    ambiguous rounding band. `forced` overrides the measured integer (--offset).
    """
    offset_s = (stamp_ns - recv_ns) / 1e9
    n = forced if forced is not None else round(offset_s)
    frac = abs(offset_s - round(offset_s))
    ambiguous = AMBIG_LO <= frac <= AMBIG_HI
    return n, stamp_ns - n * NS, ambiguous


def build_histogram(offsets):
    """Count integer offsets: list[int] -> {int: count}."""
    hist = {}
    for n in offsets:
        hist[n] = hist.get(n, 0) + 1
    return hist


def print_histogram(hist):
    """Print one line per integer-second offset, ascending."""
    if not hist:
        print('  (no M3 detection messages)')
        return
    for n in sorted(hist):
        print(f'  {n:+d} s: {hist[n]}')


def rewrite_tf(msg):
    """Set the bizzy/m3 transform's translation in a TFMessage; rotation untouched.

    Returns True if a matching transform was found and rewritten.
    """
    changed = False
    for tr in msg.transforms:
        if tr.child_frame_id == M3_FRAME:
            tr.transform.translation.x = M3_XYZ[0]
            tr.transform.translation.y = M3_XYZ[1]
            tr.transform.translation.z = M3_XYZ[2]
            changed = True
    return changed


def detect_storage(path):
    """Storage id for opening: 'mcap' for a bare .mcap file, '' (auto) for a dir."""
    if os.path.isdir(path):
        return ''
    if path.endswith('.mcap'):
        return 'mcap'
    return ''


def path_size(path):
    """Total bytes of a bag file or directory (0 if missing)."""
    if os.path.isfile(path):
        return os.path.getsize(path)
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))
    return total


def validate_written(path, storage_id):
    """Confirm a freshly-written bag is loadable before we trust it.

    Opens a SequentialReader and reads one message (an empty-but-openable bag is
    still valid). On any failure, falls back to a size>0 heuristic and WARNs that
    validation was degraded. Returns True if the output is considered usable.
    """
    try:
        rd = SequentialReader()
        rd.open(StorageOptions(uri=path, storage_id=storage_id), ConverterOptions('', ''))
        if rd.has_next():
            rd.read_next()
        del rd
        return True
    except Exception as exc:                       # noqa: BLE001 - degrade, don't crash
        if path_size(path) > 0:
            print(f'WARN: could not open written bag for validation ({exc}); '
                  f'falling back to size>0 check (passed)', file=sys.stderr)
            return True
        print(f'ERROR: written bag failed validation and is empty ({exc})', file=sys.stderr)
        return False


def stream(rd, wr, msgcls, a, counters, offsets):
    """Read every message; correct the two target topics, pass the rest through.

    `wr` may be None (report-only): corrections are counted but nothing is written.
    """
    while rd.has_next():
        topic, data, ts = rd.read_next()
        if topic == M3_DETECTIONS_TOPIC and not a.no_timing:
            m = deserialize_message(data, msgcls[topic])
            stamp_ns = m.header.stamp.sec * NS + m.header.stamp.nanosec
            n, new_ns, ambiguous = correct_stamp(stamp_ns, ts, a.offset)
            offsets.append(n)
            if ambiguous:
                counters['ambiguous'] += 1
                print(f'WARN: ping offset {(stamp_ns - ts) / 1e9:+.3f}s is near a '
                      f'rounding boundary (applied n={n:+d}s)', file=sys.stderr)
            if n != 0:
                m.header.stamp.sec = new_ns // NS
                m.header.stamp.nanosec = new_ns % NS
                counters['timing'] += 1
                if wr:
                    wr.write(topic, serialize_message(m), ts)
            else:
                counters['pass'] += 1
                if wr:
                    wr.write(topic, data, ts)          # unchanged -> byte passthrough
        elif topic == TF_STATIC_TOPIC and not a.no_tf:
            m = deserialize_message(data, msgcls[topic])
            if rewrite_tf(m):
                counters['tf'] += 1
                if wr:
                    wr.write(topic, serialize_message(m), ts)
            else:
                counters['pass'] += 1
                if wr:
                    wr.write(topic, data, ts)
        else:
            counters['pass'] += 1
            if wr:
                wr.write(topic, data, ts)


def open_reader(path):
    """Open a SequentialReader; return (reader, storage_identifier, topics, msgcls)."""
    rd = SequentialReader()
    rd.open(StorageOptions(uri=path, storage_id=detect_storage(path)),
            ConverterOptions('', ''))
    sid = rd.get_metadata().storage_identifier
    if not sid:                                        # don't silently change format
        sys.exit('could not determine input bag storage format')
    topics = rd.get_all_topics_and_types()
    msgcls = {t.name: get_message(t.type) for t in topics}
    return rd, sid, topics, msgcls


def write_bag(out, sid, topics, rd, msgcls, a, counters, offsets):
    """Stream rd into a new bag at `out` (storage `sid`), cleaning up on failure."""
    wr = SequentialWriter()
    wr.open(StorageOptions(uri=out, storage_id=sid), ConverterOptions('', ''))
    for t in topics:                                   # preserve type, QoS, hash
        wr.create_topic(t)
    ok = False
    try:
        stream(rd, wr, msgcls, a, counters, offsets)
        ok = True
    finally:
        del wr                                         # finalize the writer once
        if not ok and os.path.exists(out):
            _remove(out)                               # no partial bag left behind


def _remove(path):
    """Remove a bag path (file or directory)."""
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)


def inplace_paths(in_bag):
    """(temp, backup) paths for an in-place retrofit, matching the input form."""
    if os.path.isdir(in_bag):
        return in_bag + '.tmp', in_bag + '.orig'
    stem = in_bag[:-len('.mcap')] if in_bag.endswith('.mcap') else in_bag
    suffix = '.mcap' if in_bag.endswith('.mcap') else ''
    return stem + '.tmp' + suffix, stem + '.orig' + suffix


def parse_args(argv=None):
    """Parse command-line arguments."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('in_bag')
    ap.add_argument('--out', help='write a non-destructive sibling here instead of in-place')
    ap.add_argument('--report-only', action='store_true',
                    help='print the offset histogram + counts without writing')
    ap.add_argument('--offset', type=int, default=None,
                    help='force this integer-second shift on every M3 ping')
    ap.add_argument('--no-tf', action='store_true', help='skip the tf_static geometry fix')
    ap.add_argument('--no-timing', action='store_true', help='skip the detection timing fix')
    return ap.parse_args(argv)


def main(argv=None):
    """Retrofit one M3 bag (geometry + timing); in-place with backup by default."""
    a = parse_args(argv)
    in_bag = a.in_bag.rstrip('/')
    if not os.path.exists(in_bag):
        sys.exit(f'input bag not found: {in_bag}')

    counters = {'tf': 0, 'timing': 0, 'pass': 0, 'ambiguous': 0}
    offsets = []

    # --- report-only: stream without writing -------------------------------
    if a.report_only:
        rd, _sid, _topics, msgcls = open_reader(in_bag)
        stream(rd, None, msgcls, a, counters, offsets)
        _summary(in_bag, None, counters, offsets, a, wrote=False)
        # Non-zero exit if any correction WOULD apply (batch "needs fixing?" probe).
        return 2 if (counters['tf'] or counters['timing']) else 0

    # --- determine output path ---------------------------------------------
    if a.out:
        out = a.out.rstrip('/')
        if os.path.exists(out):
            sys.exit(f'output already exists: {out}')
        target = out
    else:
        temp, backup = inplace_paths(in_bag)
        if os.path.exists(temp):
            sys.exit(f'temp path already exists: {temp}')
        if os.path.exists(backup):
            sys.exit(f'backup already exists (refusing to overwrite): {backup}')
        out = temp
        target = in_bag

    # --- write --------------------------------------------------------------
    rd, sid, topics, msgcls = open_reader(in_bag)
    write_bag(out, sid, topics, rd, msgcls, a, counters, offsets)

    # --- validate then (for in-place) swap in -------------------------------
    if not validate_written(out, sid):
        _remove(out)
        sys.exit('aborting: written bag failed validation; original untouched')

    if not a.out:
        os.rename(in_bag, backup)                      # preserve original first
        os.rename(out, in_bag)                         # then move corrected into place
        _summary(in_bag, backup, counters, offsets, a, wrote=True)
    else:
        _summary(target, None, counters, offsets, a, wrote=True)
    return 0


def _summary(target, backup, counters, offsets, a, wrote):
    """Print the histogram and a one-line outcome."""
    print('integer-second offset histogram (M3 detections):')
    print_histogram(build_histogram(offsets))
    verb = 'wrote' if wrote else 'would correct'
    print(f'{verb}: {counters["tf"]} tf_static, {counters["timing"]} timing; '
          f'{counters["pass"]} passthrough; {counters["ambiguous"]} ambiguous-band WARN')
    if wrote:
        print(f'  -> {target}')
        if backup:
            print(f'  backup: {backup}')
    if not a.no_timing and not a.no_tf and not counters['tf'] and not counters['timing']:
        print('NOTE: nothing matched -- no /tf_static bizzy/m3 frame and no M3 '
              'detection corrections. Is this an M3 bag?', file=sys.stderr)


if __name__ == '__main__':
    sys.exit(main())
