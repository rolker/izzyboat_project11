#!/usr/bin/env python3
"""Get earth->map transform from bag, convert track to lat/lon."""
import rosbag2_py, numpy as np, math
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
from scipy.spatial.transform import Rotation as R

BAG = "/home/roland/data/logs/gabby/logs/bizzy_images/bag_2026-07-20T13.45.16_ffmpeg_seg"
import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
reader = rosbag2_py.SequentialReader()
reader.open(rosbag2_py.StorageOptions(uri=BAG, storage_id="mcap"), rosbag2_py.ConverterOptions("",""))
topics = {t.name: t.type for t in reader.get_all_topics_and_types()}
Tem = None
while reader.has_next():
    topic, data, ts = reader.read_next()
    if topic == "/tf":
        msg = deserialize_message(data, get_message(topics[topic]))
        for tr in msg.transforms:
            if tr.header.frame_id == "earth" and tr.child_frame_id == "bizzy/map":
                q = tr.transform.rotation; v = tr.transform.translation
                Tem = (np.array([q.x,q.y,q.z,q.w]), np.array([v.x,v.y,v.z]))
                break
    if Tem: break
q, t = Tem
print("earth->map t:", t, " q:", q)

def ecef2lla(p):
    a=6378137.0; f=1/298.257223563; e2=f*(2-f)
    X,Y,Z=p; lon=math.atan2(Y,X); r=math.hypot(X,Y)
    lat=math.atan2(Z, r*(1-e2))
    for _ in range(6):
        N=a/math.sqrt(1-e2*math.sin(lat)**2)
        h=r/math.cos(lat)-N
        lat=math.atan2(Z, r*(1-e2*N/(N+h)))
    return math.degrees(lat), math.degrees(lon), h

Rm = R.from_quat(q)
d = np.load(f"{OUT}/waterline_obs.npz")
pos = d["pos_xyz"]
lls = [ecef2lla(t + Rm.apply(p)) for p in pos[::300]]
for la,lo,h in lls[:3]: print(f"lat={la:.6f} lon={lo:.6f} h={h:.1f}")
lats=[l[0] for l in lls]; lons=[l[1] for l in lls]
print(f"track bbox: lat {min(lats):.5f}..{max(lats):.5f}, lon {min(lons):.5f}..{max(lons):.5f}")
np.savez(f"{OUT}/earth_map.npz", q=q, t=t)
