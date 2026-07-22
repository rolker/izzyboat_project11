#!/usr/bin/env python3
"""Stage 1: extract waterline boundary rows (sub-pixel) per column per frame for all 4 cameras,
plus TF attitude/position tracks and static camera chains. Saves NPZ for stage-2 solve."""
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message
import numpy as np
import os

BAG = os.environ.get("CAMERA_CAL_BAG",
                     "/home/roland/data/logs/gabby/logs/bizzy_images/bag_2026-07-20T13.45.16_ffmpeg_seg")
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
CAMS = ["oak_forward", "oak_aft", "oak_port", "oak_starboard"]
SEGT = {f"/bizzy/sensors/cameras/{c}/segmentation": i for i, c in enumerate(CAMS)}
CIT = {f"/bizzy/sensors/cameras/{c}/segmentation/camera_info": i for i, c in enumerate(CAMS)}

reader = rosbag2_py.SequentialReader()
reader.open(rosbag2_py.StorageOptions(uri=BAG, storage_id="mcap"),
            rosbag2_py.ConverterOptions("", ""))
topics = {t.name: t.type for t in reader.get_all_topics_and_types()}

frames = [[] for _ in CAMS]      # (stamp, boundary[128] float32, valid[128] bool)
caminfo = [None]*4               # (K, D)
att_t, att_q = [], []            # north_up -> base_link quat (x,y,z,w)
pos_t, pos_xyz = [], []          # map -> base_link_north_up translation
static_tf = {}                   # child -> (parent, q, t)

def stamp(h):
    return h.stamp.sec + h.stamp.nanosec*1e-9

while reader.has_next():
    topic, data, ts = reader.read_next()
    if topic in SEGT:
        i = SEGT[topic]
        msg = deserialize_message(data, get_message(topics[topic]))
        img = np.frombuffer(msg.data, dtype=np.uint8).reshape(96, 128, 3).astype(np.int16)
        G = img[:,:,1]; other = np.maximum(img[:,:,0], img[:,:,2])
        g = G - other                      # >0 = water
        green = g > 0
        # contiguous green run touching the bottom
        runlen = green[::-1].cumprod(axis=0).sum(axis=0)   # per column
        valid = (runlen > 3) & (runlen < 96)
        b = 95 - runlen                    # first non-green row above the run (row index)
        b_cl = np.clip(b, 0, 94)
        cols = np.arange(128)
        g_above = g[b_cl, cols].astype(np.float32)         # <=0
        g_below = g[np.clip(b_cl+1, 0, 95), cols].astype(np.float32)  # >0
        denom = g_below - g_above
        frac = np.where(denom > 0, g_below/np.maximum(denom, 1e-6), 0.5)
        subrow = (b_cl + 1 - frac).astype(np.float32)      # boundary row (subpixel)
        frames[i].append((stamp(msg.header), subrow, valid))
    elif topic in CIT:
        i = CIT[topic]
        if caminfo[i] is None:
            msg = deserialize_message(data, get_message(topics[topic]))
            caminfo[i] = (np.array(msg.k).reshape(3,3), np.array(msg.d))
    elif topic == "/tf":
        msg = deserialize_message(data, get_message(topics[topic]))
        for tr in msg.transforms:
            q = tr.transform.rotation; v = tr.transform.translation
            if tr.child_frame_id == "bizzy/base_link" and tr.header.frame_id == "bizzy/base_link_north_up":
                att_t.append(stamp(tr.header)); att_q.append((q.x,q.y,q.z,q.w))
            elif tr.child_frame_id == "bizzy/base_link_north_up" and tr.header.frame_id == "bizzy/map":
                pos_t.append(stamp(tr.header)); pos_xyz.append((v.x,v.y,v.z))
    elif topic == "/tf_static":
        msg = deserialize_message(data, get_message(topics[topic]))
        for tr in msg.transforms:
            q = tr.transform.rotation; v = tr.transform.translation
            static_tf[tr.child_frame_id] = (tr.header.frame_id,
                np.array([q.x,q.y,q.z,q.w]), np.array([v.x,v.y,v.z]))

save = {}
for i, c in enumerate(CAMS):
    fr = frames[i]
    save[f"{c}_t"] = np.array([f[0] for f in fr])
    save[f"{c}_row"] = np.stack([f[1] for f in fr])
    save[f"{c}_valid"] = np.stack([f[2] for f in fr])
    save[f"{c}_K"] = caminfo[i][0]; save[f"{c}_D"] = caminfo[i][1]
    print(f"{c}: {len(fr)} frames, valid cols {save[f'{c}_valid'].mean()*100:.1f}%")
save["att_t"] = np.array(att_t); save["att_q"] = np.array(att_q)
save["pos_t"] = np.array(pos_t); save["pos_xyz"] = np.array(pos_xyz)
# static chains for cameras: base_link -> camera_mast -> oak_X -> optical
import json
chains = {}
for c in CAMS:
    chain = []
    f = f"bizzy/{c}_optical"
    while f != "bizzy/base_link":
        parent, q, t = static_tf[f]
        chain.append((f, list(q), list(t)))
        f = parent
    chains[c] = chain[::-1]
save["chains_json"] = np.array(json.dumps(chains))
np.savez_compressed(f"{OUT}/waterline_obs.npz", **save)
print(f"attitude samples {len(att_t)}, position samples {len(pos_t)}")
print("saved waterline_obs.npz")
