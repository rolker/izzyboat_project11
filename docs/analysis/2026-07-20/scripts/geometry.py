#!/usr/bin/env python3
"""Stage 2a: turn waterline rows into observations (elevation in level frame, world azimuth,
in-camera horizontal angle, boat position) using bag TF. Saves obs.npz."""
import numpy as np, json, cv2
from scipy.spatial.transform import Rotation as R, Slerp

import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
d = np.load(f"{OUT}/waterline_obs.npz", allow_pickle=True)
CAMS = ["oak_forward", "oak_aft", "oak_port", "oak_starboard"]
chains = json.loads(str(d["chains_json"]))

att_t = d["att_t"]; att_q = d["att_q"]; pos_t = d["pos_t"]; pos_xyz = d["pos_xyz"]
slerp = Slerp(att_t, R.from_quat(att_q))

# static rotation optical->base_link and camera position in base_link, per camera
R_bl_opt = {}; t_bl_cam = {}
for c in CAMS:
    Rc = R.identity(); tc = np.zeros(3)
    for name, q, t in chains[c]:
        Rj = R.from_quat(q)          # parent<-child rotation
        tc = tc + Rc.apply(np.array(t))
        Rc = Rc * Rj
    R_bl_opt[c] = Rc; t_bl_cam[c] = tc
    fb = Rc.apply([0,0,1])           # optical +z (view dir) in base_link
    print(f"{c}: cam pos bl={tc.round(3)}, view dir bl={fb.round(4)}, "
          f"down-tilt={np.degrees(np.arcsin(-fb[2]/np.linalg.norm(fb))):.2f} deg")

# water plane z in map: mean over bag of (base_link origin z + rotated (0,0,0.03)).z
Ratt_all = slerp(np.clip(pos_t, att_t[0], att_t[-1]))
wl_z = pos_xyz[:,2] + Ratt_all.apply(np.tile([0,0,0.03],(len(pos_t),1)))[:,2]
water_z = np.median(wl_z)
print(f"water plane z (map) = {water_z:.3f} (std {wl_z.std():.3f})")

obs = {k: [] for k in ["cam","t","el","az","u","x","y","h","psi"]}
for ci, c in enumerate(CAMS):
    t = d[f"{c}_t"]; rows = d[f"{c}_row"]; valid = d[f"{c}_valid"]
    K = d[f"{c}_K"]; D = d[f"{c}_D"]
    nF = len(t); cols = np.arange(128, dtype=np.float64)
    # undistort all points at once
    pts = np.stack([np.tile(cols, nF), rows.ravel()], axis=1).astype(np.float64)
    und = cv2.undistortPoints(pts.reshape(-1,1,2), K, D).reshape(-1,2)  # normalized (x right, y down)
    rays_opt = np.column_stack([und[:,0], und[:,1], np.ones(len(und))])
    rays_bl = R_bl_opt[c].apply(rays_opt)                    # in base_link
    # in-camera horizontal angle (about optical center): u = atan(x_n)
    u = np.arctan(und[:,0])
    # clamp stamps into att range, interpolate attitude+position per frame
    tc = np.clip(t, att_t[0], att_t[-1])
    Ratt = slerp(tc)
    px = np.interp(tc, pos_t, pos_xyz[:,0]); py = np.interp(tc, pos_t, pos_xyz[:,1])
    pz = np.interp(tc, pos_t, pos_xyz[:,2])
    Rm = Ratt.as_matrix()                                    # north_up <- base_link
    rays_nu = np.einsum("fij,fcj->fci", Rm, rays_bl.reshape(nF,128,3))
    campos_nu = np.einsum("fij,j->fi", Rm, t_bl_cam[c])      # camera offset in level frame
    el = np.degrees(np.arctan2(rays_nu[:,:,2], np.hypot(rays_nu[:,:,0], rays_nu[:,:,1])))
    az = np.degrees(np.arctan2(rays_nu[:,:,1], rays_nu[:,:,0]))   # world az (map x-ref)
    # body azimuth psi of ray (for mode decomposition): from rays_bl
    psi = np.degrees(np.arctan2(rays_bl[:,1], rays_bl[:,0])).reshape(nF,128)
    h = (pz[:,None] + campos_nu[:,2:3] - water_z) * np.ones((nF,128))
    v = valid.astype(bool)
    obs["cam"].append(np.full(v.sum(), ci, dtype=np.int8))
    obs["t"].append(np.repeat(t, v.sum(axis=1) if False else 0) if False else np.repeat(t, valid.sum(axis=1)))
    obs["el"].append(el[v]); obs["az"].append(az[v]); obs["u"].append(u.reshape(nF,128)[v])
    obs["x"].append(np.repeat(px, valid.sum(axis=1))); obs["y"].append(np.repeat(py, valid.sum(axis=1)))
    obs["h"].append(h[v]); obs["psi"].append(psi[v])
    print(f"{c}: {v.sum()} obs, el mean {el[v].mean():+.3f} med {np.median(el[v]):+.3f} "
          f"p5 {np.percentile(el[v],5):+.2f} p95 {np.percentile(el[v],95):+.2f}")

O = {k: np.concatenate(vv) for k, vv in obs.items()}
np.savez_compressed(f"{OUT}/obs.npz", **O)
print(f"total obs: {len(O['el'])}")
