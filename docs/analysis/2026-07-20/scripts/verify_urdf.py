#!/usr/bin/env python3
"""Final gate: build camera chains from an expanded URDF file and re-run the
shoreline residual fit on the bag. Expect |alpha| ~ 0.01 deg, |tilt| ~ 0.01 deg.
Usage: verify_urdf.py <expanded.urdf>"""
import sys, numpy as np, json, math, cv2
import xml.etree.ElementTree as ET
from scipy.spatial.transform import Rotation as R, Slerp

import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
CAMS = ["oak_forward", "oak_aft", "oak_port", "oak_starboard"]
SHORT = ["fwd", "aft", "port", "stbd"]

if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} <expanded.urdf>", file=sys.stderr)
    sys.exit(2)

# --- parse URDF joints into parent->child transforms
tree = ET.parse(sys.argv[1])
joints = {}
for j in tree.getroot().findall("joint"):
    parent = j.find("parent").attrib["link"]; child = j.find("child").attrib["link"]
    o = j.find("origin")
    xyz = [float(v) for v in o.attrib.get("xyz","0 0 0").split()]
    rpy = [float(v) for v in o.attrib.get("rpy","0 0 0").split()]
    joints[child] = (parent, R.from_euler("ZYX", [rpy[2], rpy[1], rpy[0]]), np.array(xyz))

def chain_R_t(optical):
    Rc = R.identity(); tc = np.zeros(3)
    seq = []
    f = optical
    while f != "bizzy/base_link":
        parent, Rj, tj = joints[f]
        seq.append((Rj, tj)); f = parent
    for Rj, tj in seq[::-1]:
        tc = tc + Rc.apply(tj); Rc = Rc * Rj
    return Rc, tc

d = np.load(f"{OUT}/waterline_obs.npz", allow_pickle=True)
att_t = d["att_t"]; att_q = d["att_q"]; pos_t = d["pos_t"]; pos_xyz = d["pos_xyz"]
slerp = Slerp(att_t, R.from_quat(att_q))
em = np.load(f"{OUT}/earth_map.npz"); Rem = R.from_quat(em["q"]); tem = em["t"]

def lla2ecef(lat, lon, hh):
    a=6378137.0; f=1/298.257223563; e2=f*(2-f)
    la=math.radians(lat); lo=math.radians(lon)
    N=a/math.sqrt(1-e2*math.sin(la)**2)
    return np.array([(N+hh)*math.cos(la)*math.cos(lo),(N+hh)*math.cos(la)*math.sin(lo),
                     (N*(1-e2)+hh)*math.sin(la)])
mass = json.load(open(f"{OUT}/massabesic.json"))["elements"][0]
segs = []
for m in mass["members"]:
    if not m.get("geometry"): continue
    pts = np.array([Rem.inv().apply(lla2ecef(g["lat"],g["lon"],48.7)-tem)[:2] for g in m["geometry"]])
    segs.append(np.column_stack([pts[:-1], pts[1:]]))
S = np.vstack(segs)
x1,y1,x2,y2 = S[:,0],S[:,1],S[:,2],S[:,3]; ex=x2-x1; ey=y2-y1

wl_z = pos_xyz[:,2] + slerp(np.clip(pos_t, att_t[0], att_t[-1])).apply(np.tile([0,0,0.03],(len(pos_t),1)))[:,2]
water_z = np.median(wl_z)

print(f"{'cam':5s} {'resid_alpha':>12s} {'in-view tilt':>13s} {'scale':>7s}   (want ~0, ~0)")
worst = 0.0
for ci, c in enumerate(CAMS):
    Rc, t0 = chain_R_t(f"bizzy/{c}_optical")
    fb = Rc.apply([0,0,1])
    t = d[f"{c}_t"][::2]; rows = d[f"{c}_row"][::2]; valid = d[f"{c}_valid"][::2]
    K = d[f"{c}_K"]; D = d[f"{c}_D"]
    nF = len(t); cols = np.arange(128, dtype=np.float64)
    pts = np.stack([np.tile(cols, nF), rows.ravel()], axis=1)
    und = cv2.undistortPoints(pts.reshape(-1,1,2), K, D).reshape(-1,2)
    rays_bl = Rc.apply(np.column_stack([und[:,0], und[:,1], np.ones(len(und))]))
    u = np.degrees(np.arctan(und[:,0]))
    tc_ = np.clip(t, att_t[0], att_t[-1])
    Rm = slerp(tc_).as_matrix()
    px = np.interp(tc_, pos_t, pos_xyz[:,0]); py = np.interp(tc_, pos_t, pos_xyz[:,1])
    pz = np.interp(tc_, pos_t, pos_xyz[:,2])
    rays_nu = np.einsum("fij,fcj->fci", Rm, rays_bl.reshape(nF,128,3))
    cam_nu = np.einsum("fij,j->fi", Rm, t0)
    el = np.degrees(np.arctan2(rays_nu[:,:,2], np.hypot(rays_nu[:,:,0], rays_nu[:,:,1])))
    az = np.degrees(np.arctan2(rays_nu[:,:,1], rays_nu[:,:,0]))
    h = pz[:,None] + cam_nu[:,2:3] - water_z
    v = valid & (el > -3.0) & (el < 1.6)
    eli = el[v][::3]; azi = az[v][::3]; ui = u.reshape(nF,128)[v][::3]
    xi = np.repeat(px, v.sum(1))[::3]; yi = np.repeat(py, v.sum(1))[::3]
    hi = (h*np.ones_like(el))[v][::3]
    ddx = np.cos(np.radians(azi)); ddy = np.sin(np.radians(azi))
    Rt = np.full(len(eli), np.inf)
    for s0 in range(0, len(eli), 3000):
        sl = slice(s0, min(s0+3000, len(eli)))
        den = ddx[sl,None]*ey - ddy[sl,None]*ex
        wx = x1-xi[sl,None]; wy = y1-yi[sl,None]
        with np.errstate(divide="ignore", invalid="ignore"):
            ts_ = (wx*ey - wy*ex)/den; ss = (wx*ddy[sl,None] - wy*ddx[sl,None])/den
        Rt[sl] = np.where((den!=0)&(ss>=0)&(ss<=1)&(ts_>1), ts_, np.inf).min(1)
    ok = np.isfinite(Rt) & (Rt < 3000)
    r = eli[ok] - np.degrees(-np.arctan2(hi[ok], Rt[ok])); uo = ui[ok]
    w = np.ones(len(r))
    for _ in range(3):
        A = np.column_stack([np.ones(len(r)), uo])
        ab,*_ = np.linalg.lstsq(A*np.sqrt(w)[:,None], r*np.sqrt(w), rcond=None)
        rr = r - A@ab
        sc = 1.4826*np.median(np.abs(rr))
        w = np.minimum(1, 1.345*sc/np.maximum(np.abs(rr),1e-12))
    tilt = math.degrees(math.atan(ab[1]))
    worst = max(worst, abs(ab[0]), abs(tilt))
    print(f"{SHORT[ci]:5s} {ab[0]:+12.3f} {tilt:+13.3f} {sc:7.3f}   "
          f"(down-tilt now {np.degrees(np.arcsin(-fb[2])):.2f} deg)")
print(f"\nworst residual: {worst:.3f} deg -> {'PASS' if worst < 0.05 else 'FAIL'} (threshold 0.05)")
sys.exit(0 if worst < 0.05 else 1)
