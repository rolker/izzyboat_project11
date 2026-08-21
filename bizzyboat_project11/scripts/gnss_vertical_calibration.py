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
import math
import statistics as st
import sys
from pathlib import Path

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

# URDF, base_link frame (x fwd, z up)
FCU_ANT = (0.835, 0.890)          # gnss_forward  == GPS_POS1
SBG_ANT = (-1.073, 0.882)         # sbg_gnss_primary, surveyed w/ phase centre

TOPICS = {
    '/bizzy/mavros/gpsstatus/gps1/raw': 'fcu',
    '/bizzy/sensors/sbg/imu/nav_sat_fix': 'sbg',
    '/bizzy/mavros/imu/data': 'fcu_att',
    '/bizzy/sensors/sbg/imu/data': 'sbg_att',
    '/bizzy/odom': 'odom',
}
FIX_RTK_FIXED = 6
SBG_SIGZ_MAX = 0.020              # RTK_INT ran 0.010; float ran 0.046
MAX_AGE_NS = int(1.0e9)


def lever_z(x, z, pitch):
    """Vertical component of a body-frame lever arm at the given pitch
    (positive pitch = nose down, REP-103)."""
    return -x * math.sin(pitch) + z * math.cos(pitch)


def pitch_of(q):
    return math.asin(max(-1.0, min(1.0, 2.0 * (q.w * q.y - q.z * q.x))))


def read_bag(bag_dir, samples, bag_tag):
    files = sorted(Path(bag_dir).glob('*.mcap'),
                   key=lambda p: int(p.stem.rsplit('_', 1)[1]))
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
            topic, data, ts = reader.read_next()
            key = TOPICS[topic]
            msg = deserialize_message(data, types[topic])
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
            if len(latest) < 5:
                continue
            if any(ts - v[0] > MAX_AGE_NS for v in latest.values()):
                continue
            _, fcu_ant, fix = latest['fcu']
            _, sbg_ant, sigz = latest['sbg']
            if fix != FIX_RTK_FIXED or sigz > SBG_SIGZ_MAX:
                continue
            samples.append(dict(
                t=ts, bag=bag_tag, fcu_ant=fcu_ant, sbg_ant=sbg_ant,
                odom=latest['odom'][1],
                fp=latest['fcu_att'][1], sp=latest['sbg_att'][1]))
    return n_raw


def summarise(name, values, unit_mm=True):
    k = 1000.0 if unit_mm else 1.0
    m, sd = st.mean(values), st.pstdev(values)
    sem = sd / math.sqrt(len(values))
    print(f'  {name:52s} {m*k:+8.1f}   sd {sd*k:6.1f}   sem {sem*k:5.2f}   n={len(values)}')
    return m


def main():
    bags = sys.argv[1:]
    samples = []
    total_raw = 0
    for b in bags:
        n = read_bag(b, samples, Path(b).name)
        print(f'{Path(b).name}: {n} SBG fixes read, running total kept {len(samples)}')
        total_raw += n
    if not samples:
        print('no samples survived the quality gates')
        return

    samples.sort(key=lambda s: s['t'])
    span_h = (samples[-1]['t'] - samples[0]['t']) / 3.6e12
    print(f'\n{len(samples)} samples kept of {total_raw} '
          f'({100*len(samples)/total_raw:.1f}%), spanning {span_h:.2f} h\n')

    # --- antenna-to-antenna, reduced with a single common attitude ---------
    print('FCU minus SBG at base_link, both antennas reduced by URDF lever arms (mm):')
    v_f = [s['fcu_ant'] - lever_z(*FCU_ANT, s['fp'])
           - (s['sbg_ant'] - lever_z(*SBG_ANT, s['fp'])) for s in samples]
    v_s = [s['fcu_ant'] - lever_z(*FCU_ANT, s['sp'])
           - (s['sbg_ant'] - lever_z(*SBG_ANT, s['sp'])) for s in samples]
    a = summarise('using FCU attitude', v_f)
    b = summarise('using SBG attitude', v_s)
    print(f'  {"spread between the two attitudes":52s} {abs(a-b)*1000:8.1f}   '
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
    print(f'\n  spread of half-hourly means: {(max(drift)-min(drift))*1000:.1f} mm '
          f'-- this, not the sem, is the honest uncertainty')

    print(f'\nImplied correction: GPS_POS1_Z / GPS_POS2_Z and the URDF gnss_* z')
    print(f'  should change by {b*1000:+.0f} mm, i.e. 0.890 -> {0.890 + b:.3f} m')


main()
