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
    offset is within ~0.2 s of a half-second (frac >= 0.3, where frac in [0, 0.5]).

The integer-offset HISTOGRAM is always printed (e.g. "0 s: 412, 6 s: 1805") so
the step structure is visible and the PPS assumption is validated. It always
records the MEASURED integer offset, even under --offset, so the diagnostic stays
honest when a manual shift is forced. Use --report-only to see it without writing
(exits non-zero if any correction would apply, so it doubles as a "does this bag
need fixing?" probe in batch scripts).

Under --no-timing the offsets are STILL measured (just not applied) and a skew
assessment runs: if a real clock skew is present (a large fraction of pings on one
non-zero integer second, vs. a latency tail centred on 0 s) it is reported and the
exit code is 3 -- so skipping the timing fix on a bag that genuinely needs it is
never silent. Exit codes: 0 = clean; 2 = a correction would apply (--report-only);
3 = real skew detected under --no-timing.

File handling (default: in-place with backup) — downstream paths reference the
original bag name, so the corrected bag takes the original name and the original
is preserved as a backup. Persist-then-rename: the corrected bag is written to a
temp path and VALIDATED (open + read one message) BEFORE the original is renamed
to `<name>.orig` and the corrected bag moved into place. A failed/partial write
never replaces the original; if the final move fails the original is rolled back
from the backup. `--out PATH` instead writes a non-destructive sibling and never
touches the input.

Bag form is preserved across the in-place retrofit:
  * directory bag in  -> directory bag out (backup `<name>.orig`)
  * bare single .mcap in (boat bags) -> bare single .mcap out. rosbag2's writer
    only emits *directory* bags, so for a bare input the single inner `.mcap`
    segment is extracted to the original name and the scratch directory dropped
    (a bare .mcap carries its own schemas/channels; the rosbag2 metadata.yaml is
    not part of the bare form). A multi-segment write cannot be reduced to one
    bare file -> the script aborts and asks for --out.

Offline read/write (rosbag2), no replay. Requires a sourced ROS 2 (jazzy) env.
Storage format + QoS are preserved (writer reuses the reader's TopicMetadata).

Usage:
    python3 retrofit_m3_bag.py <in_bag> [--out OUT] [--report-only] \
        [--offset N] [--no-tf] [--no-timing] [--force]

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

# A ping whose fractional offset is this close to a half-second makes the
# round-to-nearest-second ambiguous; such pings get a WARN. `frac` ranges over
# [0, 0.5], so this is "within (0.5 - 0.3) = 0.2 s of a half-second boundary".
AMBIG_THRESHOLD = 0.3

# When the timing fix is skipped (--no-timing) we STILL measure the offsets so a
# genuinely skewed bag is not silently passed over. A real #338 clock skew puts a
# large fraction of pings on a single NON-ZERO integer second (e.g. -9 s covered
# ~100% on 2026-06-26); receive-latency jitter instead peaks at 0 s with a small
# decaying tail (largest non-zero bin ~2% on a clean pre-skew bag). A non-zero bin
# holding at least this fraction of pings is treated as a real skew to investigate.
SKEW_BIN_FRACTION = 0.05


def correct_stamp(stamp_ns, recv_ns, forced=None):
    """Compute the integer-second stamp correction, preserving the fraction.

    Returns (measured_n, applied_n, new_stamp_ns, ambiguous): the integer offset
    measured against the receive time (always, for the histogram), the integer
    actually applied (== forced when --offset is given), the corrected stamp in
    ns, and whether the raw fractional offset was in the ambiguous rounding band.
    """
    offset_s = (stamp_ns - recv_ns) / 1e9
    measured_n = round(offset_s)
    frac = abs(offset_s - measured_n)              # in [0, 0.5]
    ambiguous = frac >= AMBIG_THRESHOLD
    applied_n = forced if forced is not None else measured_n
    return measured_n, applied_n, stamp_ns - applied_n * NS, ambiguous


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


def assess_skew(hist):
    """Classify an integer-offset histogram: real clock skew vs. receive latency.

    Returns (is_skew, detail). A genuine #338 skew shows a dominant NON-ZERO
    offset -- either the most-populated bin is non-zero, or a single non-zero bin
    holds >= SKEW_BIN_FRACTION of pings (a bag that straddles a skew jump, where
    0 s may still be the plurality). Receive latency instead peaks at 0 s with a
    decaying tail, so no non-zero bin grows large.
    """
    total = sum(hist.values())
    if total == 0:
        return False, 'no M3 detections to assess'
    mode_n = max(hist, key=lambda n: hist[n])
    nonzero = {n: c for n, c in hist.items() if n != 0}
    top_nz, top_nz_frac = 0, 0.0
    if nonzero:
        top_nz = max(nonzero, key=lambda n: nonzero[n])
        top_nz_frac = nonzero[top_nz] / total
    is_skew = mode_n != 0 or top_nz_frac >= SKEW_BIN_FRACTION
    zero_frac = hist.get(0, 0) / total
    if is_skew:
        detail = (f'dominant offset {top_nz:+d} s on {top_nz_frac:.1%} of pings '
                  f'(mode {mode_n:+d} s) -- looks like a real clock skew')
    else:
        detail = (f'offset mode 0 s ({zero_frac:.1%} of pings); largest non-zero bin '
                  f'{top_nz:+d} s on {top_nz_frac:.1%} -- consistent with receive '
                  f'latency, no clock skew')
    return is_skew, detail


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
    """Return the storage id for opening: 'mcap' for a bare .mcap file, '' for a dir."""
    if os.path.isdir(path):
        return ''
    if path.endswith('.mcap'):
        return 'mcap'
    return ''


def validate_written(path):
    """Confirm a freshly-written bag is loadable: open and read one message.

    Returns True if the bag opens and (if non-empty) yields a message. An
    empty-but-openable bag is still valid. Returns False on any failure -- no
    size>0 fallback, because in destructive in-place mode a validation failure
    must abort rather than be papered over.
    """
    try:
        rd = SequentialReader()
        rd.open(StorageOptions(uri=path, storage_id=detect_storage(path)),
                ConverterOptions('', ''))
        if rd.has_next():
            rd.read_next()
        del rd
        return True
    except Exception as exc:                       # noqa: BLE001 - report + fail closed
        print(f'ERROR: written bag failed validation: {exc}', file=sys.stderr)
        return False


def stream(rd, wr, msgcls, a, counters, offsets):
    """Read every message; correct the two target topics, pass the rest through.

    `wr` may be None (report-only): corrections are counted but nothing is written.
    The histogram (`offsets`) always records the MEASURED integer offset.
    """
    while rd.has_next():
        topic, data, ts = rd.read_next()
        if topic == M3_DETECTIONS_TOPIC:
            m = deserialize_message(data, msgcls[topic])
            stamp_ns = m.header.stamp.sec * NS + m.header.stamp.nanosec
            measured_n, applied_n, new_ns, ambiguous = correct_stamp(stamp_ns, ts, a.offset)
            offsets.append(measured_n)          # always: feeds the histogram + skew check
            if a.no_timing:
                # Diagnostic-only: measure the offset so a genuinely skewed bag is
                # still caught (see assess_skew in _summary), but never touch the
                # stamp. Per-ping ambiguous WARNs are suppressed here; the
                # end-of-run skew assessment is the signal.
                counters['pass'] += 1
                if wr:
                    wr.write(topic, data, ts)
            else:
                if ambiguous:
                    counters['ambiguous'] += 1
                    print(f'WARN: ping offset {(stamp_ns - ts) / 1e9:+.3f}s is near a '
                          f'rounding boundary (measured n={measured_n:+d}s)', file=sys.stderr)
                if applied_n != 0:
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
    """Return (temp, backup) paths for an in-place retrofit, matching input form."""
    if os.path.isdir(in_bag):
        return in_bag + '.tmp', in_bag + '.orig'
    stem = in_bag[:-len('.mcap')] if in_bag.endswith('.mcap') else in_bag
    suffix = '.mcap' if in_bag.endswith('.mcap') else ''
    return stem + '.tmp' + suffix, stem + '.orig' + suffix


def _inner_mcaps(bag_dir):
    """Return the .mcap segment filenames inside a rosbag2 directory bag, sorted."""
    return sorted(f for f in os.listdir(bag_dir) if f.endswith('.mcap'))


def _swap_in_place(in_bag, temp, backup, in_is_dir):
    """Move the validated `temp` bag to `in_bag`, preserving the input form.

    Renames the original to `backup` first, then installs the corrected bag. On a
    failed install the original is rolled back from `backup`. For a bare-file
    input the single inner `.mcap` segment is extracted so the output stays a bare
    file; a multi-segment write aborts (cannot reduce to one bare file).
    """
    if not in_is_dir:
        inner = _inner_mcaps(temp)
        if len(inner) != 1:
            _remove(temp)
            sys.exit(f'cannot reduce a {len(inner)}-segment write to a bare .mcap; '
                     f'rerun with --out to keep a directory bag')

    os.rename(in_bag, backup)                          # preserve the original first
    try:
        if in_is_dir:
            os.rename(temp, in_bag)                    # dir -> dir
        else:
            shutil.move(os.path.join(temp, _inner_mcaps(temp)[0]), in_bag)  # bare -> bare
            _remove(temp)                              # drop the scratch dir + metadata.yaml
    except Exception:
        # Roll the original back so we never leave the bag only at `.orig`.
        if os.path.exists(in_bag):
            _remove(in_bag)
        os.rename(backup, in_bag)
        _remove(temp)
        raise

    if not validate_written(in_bag):
        # Corrected bag is bad after the move; restore the original.
        _remove(in_bag)
        os.rename(backup, in_bag)
        sys.exit(f'aborting: corrected bag failed post-move validation; original '
                 f'restored from {backup}')


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
    ap.add_argument('--force', action='store_true',
                    help='remove a stale leftover .tmp bag from an interrupted run')
    return ap.parse_args(argv)


def main(argv=None):
    """Retrofit one M3 bag (geometry + timing); in-place with backup by default."""
    a = parse_args(argv)
    in_bag = a.in_bag.rstrip('/')
    if not os.path.exists(in_bag):
        sys.exit(f'input bag not found: {in_bag}')
    in_is_dir = os.path.isdir(in_bag)

    counters = {'tf': 0, 'timing': 0, 'pass': 0, 'ambiguous': 0}
    offsets = []

    # --- report-only: stream without writing -------------------------------
    if a.report_only:
        rd, _sid, _topics, msgcls = open_reader(in_bag)
        stream(rd, None, msgcls, a, counters, offsets)
        del rd
        skew = _summary(in_bag, None, counters, offsets, a, wrote=False)
        # Exit codes: 3 = real skew detected under --no-timing (investigate);
        # 2 = a correction WOULD apply (batch "needs fixing?" probe); 0 = clean.
        if skew:
            return 3
        return 2 if (counters['tf'] or counters['timing']) else 0

    # --- non-destructive sibling (--out) -----------------------------------
    if a.out:
        out = a.out.rstrip('/')
        if os.path.exists(out):
            sys.exit(f'output already exists: {out}')
        rd, sid, topics, msgcls = open_reader(in_bag)
        write_bag(out, sid, topics, rd, msgcls, a, counters, offsets)
        del rd
        if not validate_written(out):
            _remove(out)
            sys.exit('aborting: written bag failed validation (input untouched)')
        skew = _summary(out, None, counters, offsets, a, wrote=True)
        return 3 if skew else 0

    # --- in-place with backup ----------------------------------------------
    temp, backup = inplace_paths(in_bag)
    if os.path.exists(temp):
        if a.force:
            _remove(temp)
        else:
            sys.exit(f'temp path already exists (stale interrupted run?): {temp}\n'
                     f'  inspect it, or rerun with --force to remove it')
    if os.path.exists(backup):
        sys.exit(f'backup already exists (refusing to overwrite): {backup}')

    rd, sid, topics, msgcls = open_reader(in_bag)
    write_bag(temp, sid, topics, rd, msgcls, a, counters, offsets)
    del rd                                             # release input before renaming
    if not validate_written(temp):
        _remove(temp)
        sys.exit('aborting: written bag failed validation; original untouched')

    _swap_in_place(in_bag, temp, backup, in_is_dir)
    skew = _summary(in_bag, backup, counters, offsets, a, wrote=True)
    return 3 if skew else 0


def _summary(target, backup, counters, offsets, a, wrote):
    """Print the histogram and a one-line outcome; under --no-timing also run and
    print the skew assessment. Returns True iff --no-timing is set AND a real clock
    skew was detected (the caller turns that into exit code 3)."""
    hist = build_histogram(offsets)
    print('integer-second offset histogram (M3 detections, measured):')
    print_histogram(hist)
    verb = 'wrote' if wrote else 'would correct'
    print(f'{verb}: {counters["tf"]} tf_static, {counters["timing"]} timing; '
          f'{counters["pass"]} passthrough; {counters["ambiguous"]} ambiguous-band WARN')
    if wrote:
        print(f'  -> {target}')
        if backup:
            print(f'  backup: {backup}')

    skew_detected = False
    if a.no_timing:
        is_skew, detail = assess_skew(hist)
        print(f'no-timing skew check: {detail}')
        if is_skew:
            skew_detected = True
            print('WARN: a real clock skew is present but the timing fix was '
                  'skipped (--no-timing) -- investigate; this bag likely needs the '
                  'timing correction.', file=sys.stderr)

    if not a.no_timing and not a.no_tf and not counters['tf'] and not counters['timing']:
        print('NOTE: nothing matched -- no /tf_static bizzy/m3 frame and no M3 '
              'detection corrections. Is this an M3 bag?', file=sys.stderr)
    return skew_detected


if __name__ == '__main__':
    sys.exit(main())
