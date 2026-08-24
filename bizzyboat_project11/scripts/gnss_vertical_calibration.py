#!/usr/bin/env python3
"""Field-calibrate the CUAV antenna vertical reference against the SBG.

The SBG chain is trustworthy end to end: its Trimble antenna offsets were
surveyed with the documented phase centre, and its two independent routes to
base_link agree to 5 mm. So the FCU-minus-SBG difference at base_link absorbs
everything unmodelled on the CUAV side -- phase centre and mounting reference
together -- as a single empirical number. That number is the correction to
GPS_POS1_Z / GPS_POS2_Z and to the URDF gnss_* frames.

Tide, waves and heave cancel: both receivers ride the same hull.

Run over every bag recorded since the switch back to MaCORS corrections.
"""
import argparse
import math
import statistics as st
import sys
from pathlib import Path

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

# URDF, base_link frame (x fwd, z UP -- REP-103). These are (x, z): the y
# offsets are omitted because both antennas are on the centreline, and
# lever_z() below is only valid while that holds -- a y offset would need roll
# as well as pitch. Asserted at startup rather than assumed.
FCU_ANT = (0.835, 0.890)          # gnss_forward  == GPS_POS1
SBG_ANT = (-1.073, 0.882)         # sbg_gnss_primary, surveyed w/ phase centre
FCU_ANT_Y = 0.0
SBG_ANT_Y = 0.0

# These are a hand copy of the URDF, and this tool's own output is what causes
# the URDF to change. They match /tf_static today; the run after anyone applies
# a correction would be reduced with stale lever arms and nothing here would
# notice. They are printed beside the result so a mismatch is at least visible
# in the output that gets pasted into a log. Reading them from the bag's
# /tf_static is the real fix and is not done here.

# ArduPilot's GPS_POS* offsets are in the autopilot body frame, which is FRD:
# its z is DOWN. The same forward antenna is therefore +0.890 in the URDF and
# -0.890 in the parameter file, and this repo's records carry both numbers
# (docs/logs/2026/2026-05-21_gabby_logs.md, bizzyboat_project11/docs/
# bizzyboat_hardware.md). A correction to the antenna height is thus written
# with OPPOSITE signs in the two places, which is why the report below prints
# each target's own new value rather than one signed delta to apply to both.
GPS_POS_Z_IS_DOWN = True

# An antenna-height error larger than this is not an antenna-height error. The
# geoid round trip that started this whole investigation is 0.626 m, so a datum
# mismatch between the two sources lands squarely above this bound -- and the
# tool would otherwise report it in the same confident millimetres as a real
# 55 mm phase-centre offset.
MAX_PLAUSIBLE_CORRECTION_M = 0.5

# Honesty gates on the corpus itself. The apparatus below reports "perfect" on
# exactly the run it was written for: half-hourly buckets mean any corpus under
# 30 minutes lands in a single bucket, so max(drift) - min(drift) is 0 and the
# tool prints "spread of half-hourly means: 0.0 mm -- this, not the sem, is the
# honest uncertainty". With one surviving sample pstdev and sem are 0 too, and
# a confident millimetre figure still prints. The planned transit re-run is
# short, so this is not hypothetical.
#
# Two populated buckets is the minimum that can show drift at all; an hour and
# 30 samples are what make the two buckets mean something rather than being an
# accident of where the boundary fell.
MIN_POPULATED_BUCKETS = 2
MIN_SAMPLES = 30
MIN_SPAN_H = 1.0
BUCKET_H = 0.5


def uncertainty_gates(n_samples, span_h, populated_buckets):
    """Name the gates this corpus fails, so 'no drift' cannot mean 'no data'.

    Returns a list of human-readable failures. Empty means the spread figure
    below is a measurement of stability rather than an artefact of a corpus too
    short to contain any.
    """
    failures = []
    if populated_buckets < MIN_POPULATED_BUCKETS:
        failures.append(
            f'only {populated_buckets} populated '
            f'{BUCKET_H*60:.0f}-minute bucket(s); drift needs at least '
            f'{MIN_POPULATED_BUCKETS}, so a spread of 0.0 mm here means '
            f'"not measured", not "stable"')
    if n_samples < MIN_SAMPLES:
        failures.append(
            f'{n_samples} samples, under the {MIN_SAMPLES} this quotes an sd '
            f'and sem from (at n=1 both are exactly 0)')
    if span_h < MIN_SPAN_H:
        failures.append(
            f'{span_h:.2f} h of data, under {MIN_SPAN_H:.1f} h; a phase-centre '
            f'offset is constant, so a short window cannot distinguish it from '
            f'whatever the ionosphere was doing')
    return failures


DEFAULT_NAMESPACE = 'bizzy'
RELATIVE_TOPICS = {
    'mavros/gpsstatus/gps1/raw': 'fcu',
    'sensors/sbg/imu/nav_sat_fix': 'sbg',
    'mavros/imu/data': 'fcu_att',
    'sensors/sbg/imu/data': 'sbg_att',
    'odom': 'odom',
}


def topics_for(namespace):
    """Absolute topic names under ``namespace``.

    Hard-coding /bizzy meant a bag from any other hull produced 'no samples
    survived the quality gates' -- indistinguishable from bad data.
    """
    prefix = namespace.strip('/')
    return {f'/{prefix}/{name}' if prefix else f'/{name}': key
            for name, key in RELATIVE_TOPICS.items()}


TOPICS = topics_for(DEFAULT_NAMESPACE)


def apply_namespace(namespace):
    global TOPICS
    TOPICS = topics_for(namespace)


FIX_RTK_FIXED = 6
SBG_SIGZ_MAX = 0.020              # RTK_INT ran 0.010; float ran 0.046

# Pairing tolerance, applied to SENSOR timestamps (message headers), not to bag
# receive timestamps.
#
# "Tide, waves and heave cancel: both receivers ride the same hull" is the whole
# premise of this comparison, and it only holds if the two fixes describe the
# same instant. Pairing at 1 s of bag-arrival time does not: a hull heaving
# +/-0.15 m at a 4 s period moves the full amplitude in a quarter period, which
# is several times the ~55 mm being measured. Receive timestamps make it worse
# still -- they carry transport and mavros queueing jitter that has nothing to
# do with when the receiver computed its solution, and on the planned transit
# re-run (underway, real heave) that error stops averaging out.
#
# The sources run at 5-10 Hz, so 0.15 s is both achievable and enough to bound
# the heave term to roughly a centimetre at that sea state. The observed skew is
# reported at the end so the assumption is checked rather than asserted.
MAX_PAIR_SKEW_NS = int(0.15e9)


def mcap_sort_key(path):
    """Order a bag's split files by their trailing index.

    rosbag2 names splits ``<bag>_0.mcap``, ``<bag>_1.mcap``, ... and they must
    be read in that order for the 'latest sample' bookkeeping to mean anything.
    A file that does not follow the convention sorts last by name rather than
    taking the whole run down with a ValueError.
    """
    stem = path.stem.rsplit('_', 1)
    if len(stem) == 2 and stem[1].isdigit():
        return (0, int(stem[1]), path.name)
    return (1, 0, path.name)


def stamp_ns(msg, bag_ts, fallbacks):
    """Sensor time from the message header, falling back to bag receive time.

    Every topic here carries a std_msgs/Header. A zero stamp means the driver
    never filled it in, and pairing on arrival time is then the only option --
    but it is counted and reported rather than passed off as sensor time.
    """
    header = getattr(msg, 'header', None)
    if header is not None:
        stamp = header.stamp.sec * 1000000000 + header.stamp.nanosec
        if stamp > 0:
            return stamp
    fallbacks[0] += 1
    return bag_ts


def lever_z(x, z, pitch):
    """Vertical component of a body-frame lever arm at the given pitch
    (positive pitch = nose down, REP-103).

    Roll is deliberately absent: with both antennas on the centreline the y
    term is zero at any roll. assert_antennas_on_centreline() is what keeps
    that true.
    """
    return -x * math.sin(pitch) + z * math.cos(pitch)


def assert_antennas_on_centreline():
    """lever_z ignores y, which is only safe while y is zero."""
    if FCU_ANT_Y != 0.0 or SBG_ANT_Y != 0.0:
        raise SystemExit(
            f'lever_z() ignores the y component, but FCU_ANT_Y={FCU_ANT_Y} '
            f'SBG_ANT_Y={SBG_ANT_Y}. An off-centreline antenna needs roll in '
            f'the reduction; fix lever_z before trusting any number below.')


def pitch_of(q):
    return math.asin(max(-1.0, min(1.0, 2.0 * (q.w * q.y - q.z * q.x))))


REJECT_REASONS = ('incomplete set', 'pair skew', 'fix not RTK fixed',
                  'sbg vertical sigma')


def mcap_files(bag_path):
    """Every .mcap under ``bag_path``, or the file itself.

    The glob was non-recursive and directory-only, so a path to a single .mcap
    -- or to a directory of dated subdirectories, which is how these are filed
    -- matched nothing and reported 'no samples survived the quality gates'.
    """
    path = Path(bag_path)
    if path.is_file():
        return [path]
    return sorted(path.rglob('*.mcap'), key=mcap_sort_key)


def read_bag(bag_dir, samples, bag_tag, fallbacks, skews, rejects, seen_topics):
    files = mcap_files(bag_dir)
    types = {}
    latest = {}
    n_raw = 0
    for f in files:
        reader = rosbag2_py.SequentialReader()
        reader.open(rosbag2_py.StorageOptions(uri=str(f), storage_id='mcap'),
                    rosbag2_py.ConverterOptions('', ''))
        for t in reader.get_all_topics_and_types():
            if t.name in TOPICS:
                types[t.name] = get_message(t.type)
        reader.set_filter(rosbag2_py.StorageFilter(topics=list(TOPICS)))
        while reader.has_next():
            topic, data, bag_ts = reader.read_next()
            key = TOPICS[topic]
            seen_topics[topic] = seen_topics.get(topic, 0) + 1
            msg = deserialize_message(data, types[topic])
            ts = stamp_ns(msg, bag_ts, fallbacks)
            if key == 'fcu':
                latest['fcu'] = (ts, msg.alt_ellipsoid / 1000.0, msg.fix_type)
            elif key == 'sbg':
                cov = msg.position_covariance[8]
                latest['sbg'] = (ts, msg.altitude, math.sqrt(cov) if cov > 0 else 9.9)
            elif key == 'odom':
                latest['odom'] = (ts, msg.pose.pose.position.z)
            else:
                latest[key] = (ts, pitch_of(msg.orientation))
                continue          # attitude alone never triggers a sample
            if key != 'sbg':
                continue
            n_raw += 1
            if len(latest) < len(TOPICS):
                rejects['incomplete set'] = rejects.get('incomplete set', 0) + 1
                continue
            # Skew against the SBG fix's own sensor time, in either direction:
            # header stamps are not monotonic across topics the way bag arrival
            # order is.
            # Signed, not absolute: the pairing is one-directional in read
            # order, so a systematic one-sided lag -- precisely what would
            # break the heave-cancels premise -- is invisible once abs() has
            # been taken. Keep the sign and report both.
            signed = max((ts - v[0] for v in latest.values()), key=abs)
            skew = abs(signed)
            if skew > MAX_PAIR_SKEW_NS:
                rejects['pair skew'] = rejects.get('pair skew', 0) + 1
                continue
            _, fcu_ant, fix = latest['fcu']
            _, sbg_ant, sigz = latest['sbg']
            if fix != FIX_RTK_FIXED:
                rejects['fix not RTK fixed'] = \
                    rejects.get('fix not RTK fixed', 0) + 1
                continue
            if sigz > SBG_SIGZ_MAX:
                rejects['sbg vertical sigma'] = \
                    rejects.get('sbg vertical sigma', 0) + 1
                continue
            skews.append(signed)
            samples.append(dict(
                t=ts, bag=bag_tag, fcu_ant=fcu_ant, sbg_ant=sbg_ant,
                odom=latest['odom'][1],
                fp=latest['fcu_att'][1], sp=latest['sbg_att'][1]))
            # Consume the set. Without this one FCU or attitude sample backs
            # several SBG-triggered samples whenever the rates differ, and n,
            # pstdev and sem then treat correlated samples as independent
            # while the half-hourly buckets over-weight the stretches where
            # the rates diverged.
            latest.clear()
    return n_raw


def summarise(name, values, unit_mm=True):
    k = 1000.0 if unit_mm else 1.0
    m = st.mean(values)
    if len(values) < 2:
        # pstdev and sem of one sample are both exactly 0, which prints as
        # millimetre-perfect agreement from a single reading.
        print(f'  {name:52s} {m*k:+8.1f}   sd    n/a   sem   n/a   n=1')
        return m
    sd = st.pstdev(values)
    sem = sd / math.sqrt(len(values))
    print(f'  {name:52s} {m*k:+8.1f}   sd {sd*k:6.1f}   sem {sem*k:5.2f}   n={len(values)}')
    return m


def corrected_antenna_height(correction_m, urdf_z=FCU_ANT[1]):
    """Where this measurement puts the CUAV forward antenna, in both frames.

    ``correction_m`` is the FCU-minus-SBG difference at base_link with z UP.
    base_link altitude is computed as ``antenna altitude - lever arm``, so a
    negative difference means the FCU path puts base_link too low, which means
    its lever arm is too long and the antenna really sits lower than the URDF
    places it. Hence ``new URDF z = urdf_z + correction``.

    ``GPS_POS1_Z`` describes the same antenna in ArduPilot's FRD body frame, so
    it is the negation -- and its edit has the opposite sign. Returns
    ``(new_urdf_z, new_gps_pos_z)`` in metres.
    """
    new_urdf_z = urdf_z + correction_m
    return new_urdf_z, -new_urdf_z


def correction_report(correction_m, urdf_z=FCU_ANT[1], gate_failures=()):
    """The lines an operator copies. Kept separate so the signs are testable.

    Printing one signed delta for both targets was wrong and dangerous: applied
    to GPS_POS1_Z = -0.890 it moves the antenna the wrong way, ADDING about
    110 mm to the FCU vertical path instead of removing 55 mm. Each target gets
    its own before/after value, with the frame that fixes its sign named beside
    it.
    """
    if abs(correction_m) > MAX_PLAUSIBLE_CORRECTION_M:
        return [
            '',
            f'REFUSING to quote a correction: measured {correction_m*1000:+.0f} mm, '
            f'over the {MAX_PLAUSIBLE_CORRECTION_M*1000:.0f} mm plausibility bound.',
            '  A discrepancy this size is not an antenna mounting height. Likely',
            '  causes, in order: the two altitude sources are on different datums',
            '  (the mavros geoid round trip is 0.626 m, and gpsstatus/gps1/raw',
            '  alt_ellipsoid is the field that avoids it); a lever arm in this',
            '  file no longer matches the URDF; or the bags are from another hull.',
        ]
    new_urdf_z, new_gps_pos_z = corrected_antenna_height(correction_m, urdf_z)
    old_gps_pos_z = -urdf_z
    header = []
    if gate_failures:
        header = ['', 'PROVISIONAL -- do not write these values anywhere. '
                      'The corpus does not support them:']
        header += [f'    - {failure}' for failure in gate_failures]
    return header + [
        '',
        f'Implied correction to the CUAV forward antenna height '
        f'({correction_m*1000:+.0f} mm measured at base_link, z up):',
        '',
        f'  {"URDF gnss_forward z":<22}{"(base_link, z UP)":<30}'
        f'{urdf_z:+.3f} -> {new_urdf_z:+.3f} m  '
        f'({(new_urdf_z - urdf_z)*1000:+.0f} mm)',
        f'  {"GPS_POS1_Z":<22}{"(ArduPilot body FRD, z DOWN)":<30}'
        f'{old_gps_pos_z:+.3f} -> {new_gps_pos_z:+.3f} m  '
        f'({(new_gps_pos_z - old_gps_pos_z)*1000:+.0f} mm)',
        '',
        '  The two edits carry OPPOSITE signs because the two frames do. Writing',
        '  the z-up number into GPS_POS1_Z moves the antenna the wrong way and',
        '  roughly doubles the error rather than removing it.',
        '',
        '  GPS_POS2_Z (aft antenna) is NOT covered by this measurement: only the',
        '  forward antenna was compared against the SBG. It currently carries the',
        '  same -0.890, so if the two masts are identical the same edit applies --',
        '  but that is an assumption, not a result.',
        '',
        '  This is a measurement, not a recommendation. Compare it against the',
        '  spread above before writing it anywhere, and note that GPS_POS1_Z also',
        '  affects horizontal lever-arm compensation during turns.',
    ]


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Bags are rosbag2 directories or single .mcap files. Reads '
               f'{", ".join(sorted(TOPICS))}.')
    parser.add_argument('bags', nargs='+', metavar='BAG',
                        help='rosbag2 directory (searched recursively) or '
                             '.mcap file')
    parser.add_argument('--namespace', default=DEFAULT_NAMESPACE,
                        help='robot namespace the topics live under '
                             f'(default: {DEFAULT_NAMESPACE})')
    return parser.parse_args(argv)


def report_empty_corpus(bags, seen_topics, rejects, total_raw):
    """Say which of the six ways to get nothing actually happened.

    One message, 'no samples survived the quality gates', covered a bag path
    that matched no files, a namespace this run does not use, a topic the
    recording never had, and four different quality gates. Several of those are
    wrong-input rather than bad-data, and the operator could not tell which.
    """
    lines = ['', 'no samples survived the quality gates. What was seen:']
    for bag in bags:
        path = Path(bag)
        if not path.exists():
            lines.append(f'  {bag}: does not exist')
        elif not mcap_files(path):
            lines.append(f'  {bag}: directory contains no .mcap files')
        else:
            lines.append(f'  {bag}: read')
    if not seen_topics:
        lines.append('  no messages on ANY expected topic. Either the '
                     'namespace is wrong (--namespace) or these bags are from')
        lines.append('  a different recording profile. Expected: '
                     + ', '.join(sorted(TOPICS)))
    else:
        lines.append('  messages per topic:')
        for topic in sorted(TOPICS):
            lines.append(f'    {topic:48s} {seen_topics.get(topic, 0)}')
        missing = [t for t in TOPICS if not seen_topics.get(t)]
        if missing:
            lines.append('  MISSING (a sample needs all five): '
                         + ', '.join(sorted(missing)))
    if total_raw:
        lines.append(f'  {total_raw} SBG fixes reached the quality gates and '
                     f'were rejected:')
        for reason in REJECT_REASONS:
            lines.append(f'    {reason:24s} {rejects.get(reason, 0)}')
    return lines


def main(argv=None):
    assert_antennas_on_centreline()
    args = parse_args(sys.argv[1:] if argv is None else argv)
    apply_namespace(args.namespace)
    bags = args.bags
    samples = []
    skews = []
    fallbacks = [0]
    rejects = {}
    seen_topics = {}
    total_raw = 0
    for bag in bags:
        n = read_bag(bag, samples, Path(bag).name, fallbacks, skews,
                     rejects, seen_topics)
        print(f'{Path(bag).name}: {n} SBG fixes read, '
              f'running total kept {len(samples)}')
        total_raw += n
    if not samples:
        for line in report_empty_corpus(bags, seen_topics, rejects, total_raw):
            print(line)
        return 1

    samples.sort(key=lambda s: s['t'])
    span_h = (samples[-1]['t'] - samples[0]['t']) / 3.6e12
    print(f'\n{len(samples)} samples kept of {total_raw} '
          f'({100*len(samples)/total_raw:.1f}%), spanning {span_h:.2f} h')
    # The heave-cancels premise stands or falls on this number, so print it.
    print(f'  pairing skew (sensor time): signed mean '
          f'{st.mean(skews)/1e6:+.0f} ms, max |skew| '
          f'{max(abs(k) for k in skews)/1e6:.0f} ms, tolerance '
          f'{MAX_PAIR_SKEW_NS/1e6:.0f} ms')
    print('    (signed, because pairing is one-directional in read order: a '
          'systematic one-sided lag is\n     exactly what would break the '
          'heave-cancels premise, and abs() hides it)')
    print(f'  lever arms used (URDF, base_link z up): '
          f'FCU {FCU_ANT[1]:+.3f} m at x {FCU_ANT[0]:+.3f}, '
          f'SBG {SBG_ANT[1]:+.3f} m at x {SBG_ANT[0]:+.3f}')
    print('    (hand-copied from the URDF; if a correction has since been '
          'applied these are stale)')
    if fallbacks[0]:
        print(f'  WARNING: {fallbacks[0]} messages had no header stamp and were '
              f'paired on bag receive time instead')
    print()

    # --- antenna-to-antenna, reduced with a single common attitude ---------
    print('FCU minus SBG at base_link, both antennas reduced by URDF lever arms (mm):')
    v_f = [s['fcu_ant'] - lever_z(*FCU_ANT, s['fp'])
           - (s['sbg_ant'] - lever_z(*SBG_ANT, s['fp'])) for s in samples]
    v_s = [s['fcu_ant'] - lever_z(*FCU_ANT, s['sp'])
           - (s['sbg_ant'] - lever_z(*SBG_ANT, s['sp'])) for s in samples]
    with_fcu_attitude = summarise('using FCU attitude', v_f)
    with_sbg_attitude = summarise('using SBG attitude', v_s)
    print(f'  {"spread between the two attitudes":52s} '
          f'{abs(with_fcu_attitude - with_sbg_attitude)*1000:8.1f}   '
          f'(= the IMUs\' pitch disagreement at 33 mm/deg)')

    # --- FCU EKF reduction vs SBG, less sensitive to attitude -------------
    # odom.z is the FCU's own reduction through GPS_POS1, so no assumed pitch
    # enters on that side; only the SBG's 1.073 m lever does, at ~19 mm/deg.
    print('\nFCU EKF (odom.z) minus SBG at base_link, per recording epoch (mm):')
    for tag in sorted({s['bag'] for s in samples}):
        sub = [s for s in samples if s['bag'] == tag]
        v = [s['odom'] - (s['sbg_ant'] - lever_z(*SBG_ANT, s['sp'])) for s in sub]
        summarise(tag, v)
    print('  (epochs differ by the 0.626 m geoid fix that went live at 17:01 UTC)')

    # The quoted correction pools every bag, while the section above is split
    # per bag because a config change landed mid-corpus. Print the quoted
    # quantity per bag too, so a mid-corpus change in THIS number is visible
    # rather than averaged away.
    print('\nAntenna-to-antenna difference, SBG attitude, per recording epoch (mm):')
    by_bag = {}
    for sample, value in zip(samples, v_s):
        by_bag.setdefault(sample['bag'], []).append(value)
    for tag in sorted(by_bag):
        summarise(tag, by_bag[tag])

    # --- stability over time ----------------------------------------------
    print('\nHalf-hourly means of the antenna-to-antenna difference, SBG attitude (mm):')
    t0 = samples[0]['t']
    buckets = {}
    for s, v in zip(samples, v_s):
        buckets.setdefault(int((s['t'] - t0) / 1.8e12), []).append(v)
    for k in sorted(buckets):
        vals = buckets[k]
        print(f'    +{k*0.5:4.1f} h  {st.mean(vals)*1000:+8.1f}   '
              f'sd {st.pstdev(vals)*1000:6.1f}   n={len(vals)}')
    drift = [st.mean(buckets[k]) for k in sorted(buckets)]
    gate_failures = uncertainty_gates(len(samples), span_h, len(buckets))
    if len(drift) >= MIN_POPULATED_BUCKETS:
        print(f'\n  spread of half-hourly means: '
              f'{(max(drift)-min(drift))*1000:.1f} mm '
              f'-- this, not the sem, is the honest uncertainty')
    else:
        # Printing 0.0 mm here is how the tool told itself it was perfect.
        print(f'\n  spread of half-hourly means: NOT MEASURED '
              f'({len(drift)} populated bucket) -- a single bucket cannot show '
              f'drift, and 0.0 mm would read as stability')
    if gate_failures:
        print('\n  This corpus does not support a quoted correction:')
        for failure in gate_failures:
            print(f'    - {failure}')

    # The SBG-attitude reduction is the one quoted: no assumed FCU pitch enters
    # the side being corrected.
    correction = with_sbg_attitude
    for line in correction_report(correction, gate_failures=gate_failures):
        print(line)


if __name__ == '__main__':
    sys.exit(main() or 0)
