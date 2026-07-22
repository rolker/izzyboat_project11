#!/usr/bin/env python3
"""Stage 3: absolute calibration against real OSM shoreline.
Ray-cast obs to shoreline -> el_pred = -atan(h/R); fit absolute per-camera offsets."""
import numpy as np, json, math
from scipy.spatial.transform import Rotation as R

import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
CAMS = ["fwd", "aft", "port", "stbd"]

em = np.load(f"{OUT}/earth_map.npz")
Rem = R.from_quat(em["q"]); tem = em["t"]

def lla2ecef(lat, lon, h):
    a=6378137.0; f=1/298.257223563; e2=f*(2-f)
    la=math.radians(lat); lo=math.radians(lon)
    N=a/math.sqrt(1-e2*math.sin(la)**2)
    return np.array([(N+h)*math.cos(la)*math.cos(lo), (N+h)*math.cos(la)*math.sin(lo),
                     (N*(1-e2)+h)*math.sin(la)])

d = json.load(open(f"{OUT}/massabesic.json"))
rel = d["elements"][0]
segs = []
for m in rel["members"]:
    geo = m.get("geometry")
    if not geo: continue
    pts = np.array([Rem.inv().apply(lla2ecef(g["lat"], g["lon"], 48.7) - tem)[:2] for g in geo])
    segs.append(np.column_stack([pts[:-1], pts[1:]]))   # x1 y1 x2 y2
S = np.vstack(segs)
print(f"shoreline segments: {len(S)}")

O = np.load(f"{OUT}/obs.npz")
cam = O["cam"].astype(int); el = O["el"]; az = O["az"]; u = np.degrees(O["u"])
x = O["x"]; y = O["y"]; h = O["h"]
keep = (el > -3.0) & (el < 1.6)
idx = np.where(keep)[0][::8]         # subsample ~180k
cam, el, az, u, x, y, h = (a[idx] for a in (cam, el, az, u, x, y, h))
n = len(el); print(f"obs subsampled: {n}")

# vectorized ray/segment intersection, chunked
dx = np.cos(np.radians(az)); dy = np.sin(np.radians(az))
x1,y1,x2,y2 = S[:,0],S[:,1],S[:,2],S[:,3]
ex = x2-x1; ey = y2-y1
Rtrue = np.full(n, np.nan)
CH = 4000
for s in range(0, n, CH):
    sl = slice(s, min(s+CH, n))
    ox = x[sl,None]; oy = y[sl,None]; ddx = dx[sl,None]; ddy = dy[sl,None]
    den = ddx*ey[None,:] - ddy*ex[None,:]
    wx = x1[None,:]-ox; wy = y1[None,:]-oy
    with np.errstate(divide="ignore", invalid="ignore"):
        tseg = (wx*ey[None,:] - wy*ex[None,:])/den        # distance along ray
        sseg = (wx*ddy - wy*ddx)/den                       # position on segment
    hit = (den != 0) & (sseg >= 0) & (sseg <= 1) & (tseg > 1.0)
    tv = np.where(hit, tseg, np.inf)
    Rtrue[sl] = tv.min(axis=1)
ok = np.isfinite(Rtrue) & (Rtrue < 3000)
print(f"rays hitting shoreline: {ok.mean()*100:.1f}%  R: p5={np.percentile(Rtrue[ok],5):.0f} "
      f"med={np.median(Rtrue[ok]):.0f} p95={np.percentile(Rtrue[ok],95):.0f} m")

el_pred = np.degrees(-np.arctan2(h[ok], Rtrue[ok]))
res = el[ok] - el_pred
camk = cam[ok]; uk = u[ok]
print("\nraw (el_meas - el_pred) per camera [deg]:")
for i,c in enumerate(CAMS):
    m = camk==i
    print(f"  {c:5s}: median {np.median(res[m]):+.3f}  mean {res[m].mean():+.3f}  "
          f"std {res[m].std():.3f}  n={m.sum()}")

# robust absolute fit: res = alpha_i + beta_i*u  (Huber IRLS)
X = np.zeros((ok.sum(), 8))
for i in range(4):
    m = camk==i; X[m,i]=1; X[m,4+i]=uk[m]
w = np.ones(ok.sum())
for it in range(4):
    beta,*_ = np.linalg.lstsq(X*np.sqrt(w)[:,None], res*np.sqrt(w), rcond=None)
    r = res - X@beta
    sc = 1.4826*np.median(np.abs(r))
    w = np.minimum(1, 1.345*sc/np.maximum(np.abs(r),1e-12))
alpha = beta[:4]; brl = beta[4:]
print(f"\nrobust fit (resid scale {sc:.3f} deg):")
print("absolute per-camera elevation offset alpha [deg] (reads-high positive):",
      {CAMS[i]: round(float(alpha[i]),3) for i in range(4)})
print("in-view tilt beta [deg/deg]:", {CAMS[i]: round(float(brl[i]),4) for i in range(4)})

# mode decomposition (exact, 4 alphas -> 4 modes)
common = alpha.mean()
dp = (alpha[0]-alpha[1])/2
dr = (alpha[3]-alpha[2])/2
tw = (alpha[0]+alpha[1]-alpha[2]-alpha[3])/4
print(f"\nmodes: common={common:+.3f}  pitch(fwd-aft)/2={dp:+.3f}  "
      f"roll(stbd-port)/2={dr:+.3f}  twist={tw:+.3f} [deg]")
np.savez(f"{OUT}/absolute_solution.npz", alpha=alpha, beta=brl,
         modes=np.array([common,dp,dr,tw]), scale=sc)
