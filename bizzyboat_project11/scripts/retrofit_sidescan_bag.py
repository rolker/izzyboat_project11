#!/usr/bin/env python3
"""Retrofit a *legacy* bizzy Garmin-sidescan bag with corrected geometry + radiometry.

ONE-OFF utility. New captures do NOT need this: the garmin_sidescan driver now
stamps frequency + beamwidths (marine_tools#62) and the bizzy URDF carries the
measured grazing tilt (this repo #305). This exists only to make bags recorded
*before* those fixes reprocessable (mosaic / backscatter) with correct geometry
and radiometry. Run it manually; it is not a ROS node and is not installed.

It writes a NEW bag (the input is never modified):

  * RawSonarImage ping_info  -> frequency + rx_beamwidths (across-track, the wide
    fan, FULL -3dB, rad) + tx_beamwidths (along-track, FULL -3dB, rad), per
    channel, from the GCV-20 spec table (== the values garmin_sidescan #62 stamps).
  * tf_static  -> the three  garmin_sidescan -> _{port,starboard,down}  rotations
    replaced with the grazing-tilt geometry (port = -(pi/2+g) about X,
    starboard = +(pi/2+g), down = pi). Mount offset and all other frames untouched.
    NOTE: this fixes the STATIC mount frame only; per-ping vessel roll lives in
    the bag's localization TF (earth->base_link) and composes correctly on
    reprocessing (unh_marine_autonomy#200).

Everything else passes through byte-for-byte (storage format + QoS preserved).
Offline read/write (rosbag2), no replay. Requires a sourced ROS 2 (jazzy) env.

Usage:
    python3 retrofit_sidescan_bag.py <in_bag> [out_bag] [--grazing-deg 35] \
        [--no-beamwidths] [--no-tf] [--device gcv20]

Default out_bag is "<in_bag>_retrofit". See #307 / #305 / #185.
"""
import sys, math, argparse, os
from rosbag2_py import (SequentialReader, SequentialWriter, StorageOptions,
                        ConverterOptions)
from rclpy.serialization import deserialize_message, serialize_message
from rosidl_runtime_py.utilities import get_message

PFX = "/bizzy/sensors/sidescan/garmin_sidescan"
SONAR = {f"{PFX}/sonar_image_port": "side", f"{PFX}/sonar_image_starboard": "side",
         f"{PFX}/sonar_image_down": "down"}
# GCV-20 spec table (band-center Hz; FULL -3dB beamwidths in radians).
#   rx = across-track (wide fan), tx = along-track (narrow).  PingInfo.msg convention.
RADIO = {
    "gcv20": {"side": dict(freq=1_120_000.0, rx=math.radians(55.0), tx=math.radians(0.44)),
              "down": dict(freq=820_000.0,  rx=math.radians(46.0), tx=math.radians(0.74))},
    "gcv10": {"side": dict(freq=455_000.0, rx=math.radians(55.0), tx=math.radians(0.44)),
              "down": dict(freq=800_000.0, rx=math.radians(46.0), tx=math.radians(0.74))},
}
SIDESCAN_CHILDREN = {  # child_frame_id -> roll(grazing_rad) about mount X
    "bizzy/garmin_sidescan_port":      lambda g: -(math.pi / 2 + g),
    "bizzy/garmin_sidescan_starboard": lambda g: +(math.pi / 2 + g),
    "bizzy/garmin_sidescan_down":      lambda g: math.pi,           # unchanged
}


def quat_x(roll):
    """Quaternion for a pure rotation of `roll` about the X axis."""
    return (math.sin(roll / 2), 0.0, 0.0, math.cos(roll / 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("in_bag")
    ap.add_argument("out_bag", nargs="?")
    ap.add_argument("--grazing-deg", type=float, default=35.0)
    ap.add_argument("--device", choices=["gcv20", "gcv10"], default="gcv20")
    ap.add_argument("--no-beamwidths", action="store_true")
    ap.add_argument("--no-tf", action="store_true")
    a = ap.parse_args()
    out = a.out_bag or (a.in_bag.rstrip("/") + "_retrofit")
    if os.path.exists(out):
        sys.exit(f"output already exists: {out}")
    g = math.radians(a.grazing_deg)
    radio = RADIO[a.device]

    rd = SequentialReader(); rd.open(StorageOptions(uri=a.in_bag, storage_id=""),
                                     ConverterOptions("", ""))
    meta = rd.get_metadata()
    sid = meta.storage_identifier or "mcap"
    topics = rd.get_all_topics_and_types()
    msgcls = {t.name: get_message(t.type) for t in topics}

    wr = SequentialWriter(); wr.open(StorageOptions(uri=out, storage_id=sid),
                                     ConverterOptions("", ""))
    for t in topics:                                   # reuse reader's TopicMetadata
        wr.create_topic(t)                             # preserves type, QoS, hash

    n = dict(sonar=0, tf=0, pass_=0)
    while rd.has_next():
        topic, data, ts = rd.read_next()
        if topic in SONAR and not a.no_beamwidths:
            m = deserialize_message(data, msgcls[topic])
            spec = radio[SONAR[topic]]
            m.ping_info.frequency = spec["freq"]
            m.ping_info.rx_beamwidths = [spec["rx"]]   # across-track fan
            m.ping_info.tx_beamwidths = [spec["tx"]]   # along-track
            wr.write(topic, serialize_message(m), ts); n["sonar"] += 1
        elif topic == "/tf_static" and not a.no_tf:
            m = deserialize_message(data, msgcls[topic])
            for tr in m.transforms:
                if tr.child_frame_id in SIDESCAN_CHILDREN:
                    qx, qy, qz, qw = quat_x(SIDESCAN_CHILDREN[tr.child_frame_id](g))
                    tr.transform.rotation.x = qx; tr.transform.rotation.y = qy
                    tr.transform.rotation.z = qz; tr.transform.rotation.w = qw
            wr.write(topic, serialize_message(m), ts); n["tf"] += 1
        else:
            wr.write(topic, data, ts); n["pass_"] += 1   # byte-for-byte passthrough
    del wr
    print(f"retrofit -> {out}")
    print(f"  storage={sid}  grazing={a.grazing_deg}deg  device={a.device}")
    print(f"  rewrote: {n['sonar']} sonar (freq+beamwidths), {n['tf']} tf_static; "
          f"{n['pass_']} passthrough")


if __name__ == "__main__":
    main()
