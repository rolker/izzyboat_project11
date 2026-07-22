#!/usr/bin/env python3
"""Stage 4: apply candidate corrections to the camera chain, re-run the shoreline fit,
auto-resolve sign conventions, and emit final URDF rpy values."""
import numpy as np, json, math, cv2
from scipy.spatial.transform import Rotation as R, Slerp

import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
CAMS = ["oak_forward", "oak_aft", "oak_port", "oak_starboard"]
SHORT = ["fwd", "aft", "port", "stbd"]

d = np.load(f"{OUT}/waterline_obs.npz", allow_pickle=True)
sol = np.load(f"{OUT}/absolute_solution.npz")
alpha, beta = sol["alpha"], sol["beta"]
chains = json.loads(str(d["chains_json"]))
att_t = d["att_t"]; att_q = d["att_q"]; pos_t = d["pos_t"]; pos_xyz = d["pos_xyz"]
slerp = Slerp(att_t, R.from_quat(att_q))
em = np.load(f"{OUT}/earth_map.npz"); Rem = R.from_quat(em["q"]); tem = em["t"]

def lla2ecef(lat, lon, h):
    a=6378137.0; f=1/298.257223563; e2=f*(2-f)
    la=math.radians(lat); lo=math.radians(lon)
    N=a/math.sqrt(1-e2*math.sin(la)**2)
    return np.array([(N+h)*math.cos(la)*math.cos(lo),(N+h)*math.cos(la)*math.sin(lo),
                     (N*(1-e2)+h)*math.sin(la)])
mass = json.load(open(f"{OUT}/massabesic.json"))["elements"][0]
segs = []
for m in mass["members"]:
    if not m.get("geometry"): continue
    pts = np.array([Rem.inv().apply(lla2ecef(g["lat"],g["lon"],48.7)-tem)[:2] for g in m["geometry"]])
    segs.append(np.column_stack([pts[:-1], pts[1:]]))
S = np.vstack(segs)
x1,y1,x2,y2 = S[:,0],S[:,1],S[:,2],S[:,3]; ex=x2-x1; ey=y2-y1

def chain_R_t(c):
    Rc = R.identity(); tc = np.zeros(3)
    for name, q, t in chains[c]:
        tc = tc + Rc.apply(np.array(t)); Rc = Rc * R.from_quat(q)
    return Rc, tc

wl_z = pos_xyz[:,2] + slerp(np.clip(pos_t, att_t[0], att_t[-1])).apply(np.tile([0,0,0.03],(len(pos_t),1)))[:,2]
water_z = np.median(wl_z)

def run(sa, sb, sub=24, quiet=True):
    """sa/sb: sign multipliers for alpha (tilt about optical x) and beta (about optical z)."""
    res_all = {}
    for ci, c in enumerate(CAMS):
        R0, t0 = chain_R_t(c)
        corr = R.from_euler("xz", [sa*math.radians(alpha[ci]), sb*math.atan(beta[ci])])
        Rc = R0 * corr
        t = d[f"{c}_t"][::4]; rows = d[f"{c}_row"][::4]; valid = d[f"{c}_valid"][::4]
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
        eli = el[v][::sub//4]; azi = az[v][::sub//4]; ui = u.reshape(nF,128)[v][::sub//4]
        xi = np.repeat(px, v.sum(1))[::sub//4]; yi = np.repeat(py, v.sum(1))[::sub//4]
        hi = (h*np.ones_like(el))[v][::sub//4]
        ddx = np.cos(np.radians(azi)); ddy = np.sin(np.radians(azi))
        Rt = np.full(len(eli), np.inf)
        CH = 3000
        for s0 in range(0, len(eli), CH):
            sl = slice(s0, min(s0+CH, len(eli)))
            den = ddx[sl,None]*ey - ddy[sl,None]*ex
            wx = x1-xi[sl,None]; wy = y1-yi[sl,None]
            with np.errstate(divide="ignore", invalid="ignore"):
                ts_ = (wx*ey - wy*ex)/den; ss = (wx*ddy[sl,None] - wy*ddx[sl,None])/den
            Rt[sl] = np.where((den!=0)&(ss>=0)&(ss<=1)&(ts_>1), ts_, np.inf).min(1)
        ok = np.isfinite(Rt) & (Rt < 3000)
        r = eli[ok] - np.degrees(-np.arctan2(hi[ok], Rt[ok]))
        uo = ui[ok]
        # robust line fit r = a + b*u
        w = np.ones(len(r))
        for _ in range(3):
            A = np.column_stack([np.ones(len(r)), uo])
            ab,*_ = np.linalg.lstsq(A*np.sqrt(w)[:,None], r*np.sqrt(w), rcond=None)
            rr = r - A@ab
            sc = 1.4826*np.median(np.abs(rr))
            w = np.minimum(1, 1.345*sc/np.maximum(np.abs(rr),1e-12))
        res_all[SHORT[ci]] = (ab[0], ab[1], sc)
    score = sum(abs(v[0]) + abs(math.degrees(math.atan(v[1]))) for v in res_all.values())
    if not quiet:
        for k,(a,b,sc) in res_all.items():
            print(f"  {k:5s}: residual alpha {a:+.3f} deg, in-view tilt {math.degrees(math.atan(b)):+.3f} deg (scale {sc:.3f})")
    return score, res_all

print("sign search (subsampled):")
results = {}
for sa in (+1,-1):
    for sb in (+1,-1):
        sc, _ = run(sa, sb)
        results[(sa,sb)] = sc
        print(f"  sa={sa:+d} sb={sb:+d}: total residual score {sc:.3f} deg")
best = min(results, key=results.get)
print(f"\nbest signs: sa={best[0]:+d} sb={best[1]:+d}\nfull-res verification with best signs:")
_, final = run(*best, sub=8, quiet=False)

# --- final URDF numbers: corrected R_bl_opt -> decompose into mast rpy + per-cam mount rpy
sa, sb = best
print("\n--- URDF decomposition ---")
Rcorr = {}
for ci, c in enumerate(CAMS):
    R0, _ = chain_R_t(c)
    Rcorr[c] = R0 * R.from_euler("xz", [sa*math.radians(alpha[ci]), sb*math.atan(beta[ci])])
# camera mount chain: base -> camera_mast (P,R) -> cam (rpy mount) -> optical (fixed -90/0/-90)
Ropt = R.from_euler("ZYX", [-math.pi/2, 0, -math.pi/2])   # rpy(-1.5708 0 -1.5708) -> R = Rz*Ry*Rx
# mast rigid part: fit (pitch, roll) minimizing residual per-cam trims (small-angle: use modes)
# solve numerically: mast pitch p, roll r; per-cam mount yaw fixed (0/180/+90/-90), pitch/roll free
YAWS = {"oak_forward":0.0, "oak_aft":math.pi, "oak_port":math.pi/2, "oak_starboard":-math.pi/2}
from scipy.optimize import least_squares
def resid(params):
    p, r = params[:2]
    out = []
    Rmast = R.from_euler("ZYX", [0, p, r])
    for ci, c in enumerate(CAMS):
        # required cam-in-mast rotation:
        Rcam = Rmast.inv() * Rcorr[c] * Ropt.inv()
        z,yp,rl = Rcam.as_euler("ZYX")
        # penalty: deviation of mount pitch from design 0.09 and roll from 0 (want smallest trims), yaw from cardinal
        out += [yp-0.09, rl, (z - YAWS[c] + math.pi)%(2*math.pi) - math.pi]
    return out
ls = least_squares(resid, x0=[-0.0323, 0.0])
p_m, r_m = ls.x
print(f"mast: pitch {p_m:+.5f} rad ({math.degrees(p_m):+.3f} deg), roll {r_m:+.5f} rad ({math.degrees(r_m):+.3f} deg)")
Rmast = R.from_euler("ZYX", [0, p_m, r_m])
for c in CAMS:
    Rcam = Rmast.inv() * Rcorr[c] * Ropt.inv()
    z,yp,rl = Rcam.as_euler("ZYX")
    print(f"  {c:14s} mount rpy = ({rl:+.5f} {yp:+.5f} {z:+.5f}) rad "
          f"= roll {math.degrees(rl):+.3f} pitch {math.degrees(yp):+.3f} yaw {math.degrees(z):+.2f} deg "
          f"(trim vs design: pitch {math.degrees(yp-0.09):+.3f}, roll {math.degrees(rl):+.3f})")
