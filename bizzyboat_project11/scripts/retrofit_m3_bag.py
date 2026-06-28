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
    INTEGER-second shift that PRESERVES the sub-second fraction; the per-ping
    integer comes from a WINDOWED MAXIMUM, not a per-message round:

        measured[i] = round(stamp[i] - bag_receive_time[i])   # per-message
        n[i]        = max(measured[i-W .. i+W])                # windowed envelope
        header.stamp[i] -= n[i] seconds                        # fraction untouched

    Why the window-max: stamp-minus-receive conflates the skew with receive
    latency, so a ping delivered > 0.5 s late rounds to the WRONG second. A
    per-message round() therefore mis-shifts every late ping -- on the (pre-skew)
    2026-06-12 bag that was ~9.6k clean pings dragged off zero. But latency is
    ONE-SIDED: offset = skew - transit_delay with transit_delay >= 0, so the true
    skew is the UPPER ENVELOPE -- the max over a window of time-neighbours,
    i.e. the skew of whichever neighbour arrived least delayed. The receive clock
    (gabby) agreed with every other clock to < 2 ms (#338). Unlike a mode this
    survives sustained latency bursts (it needs only one prompt ping per window).
    The count of pings whose windowed value overrode their own per-message
    integer is reported as "window override".

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
from collections import Counter

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

# Windowed timing correction (#338). A per-message round(stamp - receive)
# conflates the integer clock skew with receive latency, so a ping delivered
# > 0.5 s late rounds to the WRONG second (this over-corrected ~9.6k clean pings on
# the 2026-06-12 bag). Latency is one-sided (offset <= skew), so each ping takes
# the MAXIMUM per-message integer over a window of its time-neighbours -- the
# upper envelope = the skew of the least-delayed neighbour (see windowed_skew).
# Half-window in PINGS (M3 ~28 Hz, so this ~401-ping window spans ~14 s) -- needs
# only one promptly-delivered ping per window; larger = more burst-robust but lags
# a drift crossing more. Tunable.
SKEW_WINDOW_HALF = 200


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


def windowed_skew(measured, half):
    """Map per-message integer offsets to a latency-robust per-ping skew.

    Receive latency is ONE-SIDED: offset = skew - transit_delay with
    transit_delay >= 0 (a ping cannot be received before it was sent, and the
    gabby receive clock is accurate to < 2 ms, #338). So offset <= skew always,
    and the true skew is the UPPER ENVELOPE of the offsets -- the MAXIMUM over a
    window of time-neighbours, recovered from whichever neighbour arrived with the
    least delay. Unlike the mode, this needs only ONE promptly-delivered ping in
    the window, so it rejects latency outliers however they cluster, including
    sustained bursts that a mode cannot survive. It lags a downward-drifting skew
    by up to half a window at a crossing, where the clock is between integers and
    +/-1 s is inherent anyway. (A ping with offset ABOVE the skew is physically
    impossible barring a clock anomaly; if one ever appears, switch max -> a high
    percentile.)

    O(n * distinct) -- the window slides with incremental counts and there are
    only a handful of distinct integers.
    """
    n = len(measured)
    if n == 0:
        return []
    counts = Counter()
    out = [0] * n
    lo, hi = 0, -1                                      # inclusive window bounds
    for i in range(n):
        want_hi = min(n - 1, i + half)
        want_lo = max(0, i - half)
        while hi < want_hi:
            hi += 1
            counts[measured[hi]] += 1
        while lo < want_lo:
            counts[measured[lo]] -= 1
            if counts[measured[lo]] == 0:
                del counts[measured[lo]]
            lo += 1
        out[i] = max(counts)                           # upper-envelope skew
    return out


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


def measure_pass(in_bag):
    """First pass: read the bag once and measure, writing nothing.

    Returns (measured, tf_hits, total):
      measured -- list[int], per-message round(stamp - receive) for each M3
                  detection in bag order (feeds the histogram, the skew check, and
                  the windowed-mode correction).
      tf_hits  -- number of /tf_static messages carrying the bizzy/m3 frame
                  (== how many the geometry fix would rewrite).
      total    -- total message count (lets report-only derive its passthrough
                  count arithmetically, without a second read).
    """
    rd, _sid, _topics, msgcls = open_reader(in_bag)
    measured, tf_hits, total = [], 0, 0
    try:
        while rd.has_next():
            topic, data, ts = rd.read_next()
            total += 1
            if topic == M3_DETECTIONS_TOPIC:
                m = deserialize_message(data, msgcls[topic])
                stamp_ns = m.header.stamp.sec * NS + m.header.stamp.nanosec
                measured.append(correct_stamp(stamp_ns, ts)[0])
            elif topic == TF_STATIC_TOPIC:
                m = deserialize_message(data, msgcls[topic])
                if any(tr.child_frame_id == M3_FRAME for tr in m.transforms):
                    tf_hits += 1
    finally:
        del rd
    return measured, tf_hits, total


def compute_applied(measured, a):
    """Per-M3-ping integer-second shift to apply: None under --no-timing; a
    constant under --offset; otherwise the latency-robust windowed mode."""
    if a.no_timing:
        return None
    if a.offset is not None:
        return [a.offset] * len(measured)
    return windowed_skew(measured, SKEW_WINDOW_HALF)


def stream(rd, wr, msgcls, a, counters, applied):
    """Second pass: write `rd` to `wr`, applying the geometry fix and the
    precomputed per-ping timing shift `applied` (None under --no-timing).

    `wr` may be None (count only, no write). M3 detections are consumed in the
    same order as measure_pass, so `applied[j]` lines up with the j-th detection.
    """
    j = 0
    while rd.has_next():
        topic, data, ts = rd.read_next()
        if topic == M3_DETECTIONS_TOPIC:
            n = 0 if applied is None else applied[j]
            j += 1
            if n != 0:
                m = deserialize_message(data, msgcls[topic])
                stamp_ns = m.header.stamp.sec * NS + m.header.stamp.nanosec
                new_ns = stamp_ns - n * NS
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


def write_bag(out, sid, topics, rd, msgcls, a, counters, applied):
    """Stream rd into a new bag at `out` (storage `sid`), cleaning up on failure."""
    wr = SequentialWriter()
    wr.open(StorageOptions(uri=out, storage_id=sid), ConverterOptions('', ''))
    for t in topics:                                   # preserve type, QoS, hash
        wr.create_topic(t)
    ok = False
    try:
        stream(rd, wr, msgcls, a, counters, applied)
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


def _rename_dir_segments(bag_dir, temp_basename, final_basename):
    """Fix segment names after an in-place directory swap.

    A directory bag is written to `<final>.tmp/`, so rosbag2 bakes that temp
    basename into the segment filenames (`<final>.tmp_0.mcap`) and metadata.yaml.
    Renaming the dir to its final name does NOT fix those, leaving a misleading
    `.tmp` in the segment name. Rename each segment to `<final>_0.mcap` and patch
    metadata.yaml so the bag uses its real name (rosbag2 reads via metadata, so
    the bag works regardless, but tools/humans assuming the `<bagname>_N.mcap`
    convention should not see a `.tmp`).
    """
    for fn in os.listdir(bag_dir):
        if fn.startswith(temp_basename) and fn.endswith('.mcap'):
            os.rename(os.path.join(bag_dir, fn),
                      os.path.join(bag_dir, final_basename + fn[len(temp_basename):]))
    meta = os.path.join(bag_dir, 'metadata.yaml')
    if os.path.exists(meta):
        with open(meta) as fh:
            text = fh.read()
        with open(meta, 'w') as fh:
            fh.write(text.replace(temp_basename, final_basename))


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
            # strip the temp basename baked into segment names + metadata
            _rename_dir_segments(in_bag, os.path.basename(temp), os.path.basename(in_bag))
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

    # --- pass 1: measure offsets + locate the geometry frame ---------------
    measured, tf_hits, total = measure_pass(in_bag)
    applied = compute_applied(measured, a)             # None under --no-timing
    override = 0 if applied is None else sum(1 for w, m in zip(applied, measured) if w != m)
    counters = {'tf': 0, 'timing': 0, 'pass': 0, 'override': override}

    # --- report-only: counts are arithmetic from pass 1, no write ----------
    if a.report_only:
        counters['tf'] = tf_hits if not a.no_tf else 0
        counters['timing'] = 0 if applied is None else sum(1 for n in applied if n != 0)
        counters['pass'] = total - counters['tf'] - counters['timing']
        skew = _summary(in_bag, None, counters, measured, a, wrote=False)
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
        write_bag(out, sid, topics, rd, msgcls, a, counters, applied)
        del rd
        if not validate_written(out):
            _remove(out)
            sys.exit('aborting: written bag failed validation (input untouched)')
        skew = _summary(out, None, counters, measured, a, wrote=True)
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
    write_bag(temp, sid, topics, rd, msgcls, a, counters, applied)
    del rd                                             # release input before renaming
    if not validate_written(temp):
        _remove(temp)
        sys.exit('aborting: written bag failed validation; original untouched')

    _swap_in_place(in_bag, temp, backup, in_is_dir)
    skew = _summary(in_bag, backup, counters, measured, a, wrote=True)
    return 3 if skew else 0


def _summary(target, backup, counters, measured, a, wrote):
    """Print the histogram and a one-line outcome; under --no-timing also run and
    print the skew assessment. Returns True iff --no-timing is set AND a real clock
    skew was detected (the caller turns that into exit code 3)."""
    hist = build_histogram(measured)
    print('integer-second offset histogram (M3 detections, measured):')
    print_histogram(hist)
    verb = 'wrote' if wrote else 'would correct'
    print(f'{verb}: {counters["tf"]} tf_static, {counters["timing"]} timing '
          f'({counters["override"]} via window override); {counters["pass"]} passthrough')
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
