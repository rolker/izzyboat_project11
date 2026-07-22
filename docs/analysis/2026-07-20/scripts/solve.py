#!/usr/bin/env python3
"""Stage 2b: fixed-effect solve for per-camera trim (alpha) + in-view roll (beta),
with scene bins (position cell x world azimuth) absorbed. Then mast-mode decomposition
and parallax sweep for the common mode."""
import numpy as np

import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
O = np.load(f"{OUT}/obs.npz")
CAMS = ["fwd", "aft", "port", "stbd"]
cam = O["cam"].astype(int); el = O["el"].copy(); az = O["az"]; u = np.degrees(O["u"])
x = O["x"]; y = O["y"]; h = O["h"]

# --- filter: plausible waterline band; kills aft wake + junk
keep = (el > -3.0) & (el < 1.6)
print(f"filter: keep {keep.sum()}/{len(el)} ({100*keep.mean():.1f}%)  dropped/cam:",
      {CAMS[i]: int(((~keep)&(cam==i)).sum()) for i in range(4)})
cam, el, az, u, x, y, h = (a[keep] for a in (cam, el, az, u, x, y, h))

# --- scene bins: 40 m position cells x 3 deg azimuth
cx = np.floor(x/40).astype(int); cy = np.floor(y/40).astype(int)
ab = np.floor((az+180)/3).astype(int) % 120
key = (cx - cx.min())*100000 + (cy - cy.min())*1000 + ab
_, bin_id, bin_cnt = np.unique(key, return_inverse=True, return_counts=True)
nb = bin_cnt.size
print(f"scene bins: {nb}, median occupancy {np.median(bin_cnt):.0f}")

# design: alpha_i (indicator) + beta_i * u
n = len(el)
X = np.zeros((n, 8))
for i in range(4):
    m = cam == i
    X[m, i] = 1.0
    X[m, 4+i] = u[m]

def within_solve(Xw, yw, bins, nb, w=None):
    if w is None: w = np.ones(len(yw))
    sw = np.bincount(bins, w, minlength=nb)
    def demean(v):
        mu = np.bincount(bins, w*v, minlength=nb)/np.maximum(sw, 1e-9)
        return v - mu[bins]
    Xd = np.column_stack([demean(Xw[:,j]) for j in range(Xw.shape[1])])
    yd = demean(yw)
    W = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(Xd*W[:,None], yd*W, rcond=None)
    return beta, yd - Xd@beta

# --- robust IRLS (Huber, 3 rounds)
w = np.ones(n)
for it in range(3):
    beta, res = within_solve(X, el, bin_id, nb, w)
    s = 1.4826*np.median(np.abs(res))
    w = np.minimum(1.0, 1.345*s/np.maximum(np.abs(res), 1e-12))
    print(f"iter {it}: scale={s:.4f} deg, resid rms={res.std():.4f}")

alpha = beta[:4] - beta[:4].mean()   # gauge: sum alpha = 0 (common mode separate)
brolls = beta[4:]
print("\nper-camera elevation trim alpha (deg, gauge sum=0):",
      {CAMS[i]: round(float(alpha[i]),3) for i in range(4)})
print("per-camera in-view tilt beta (deg el per deg horiz):",
      {CAMS[i]: round(float(brolls[i]),4) for i in range(4)})

# --- mast-mode decomposition (small-angle):
# body azimuths: fwd=0, aft=180, port=+90, stbd=-90 (ROS: +y = port)
# mast pitch residual dp (bow-up positive like existing -1.85 correction convention):
#   elevation reading: fwd reads +dp, aft reads -dp
# mast roll residual dr (starboard-down positive):
#   port reads ?, stbd reads ? -> from antisym below; cross-checks from betas.
dp_el = (alpha[0] - alpha[1]) / 2.0            # from fwd/aft elevations
dr_el = (alpha[3] - alpha[2]) / 2.0            # from stbd/port elevations (sign TBD by verify step)
twist = (alpha[0] + alpha[1] - alpha[2] - alpha[3]) / 4.0  # per-camera amplitude, matches shoreline_solve.py
print(f"\nfwd/aft antisym (pitch-like): {dp_el:+.3f} deg")
print(f"stbd/port antisym (roll-like): {dr_el:+.3f} deg")
print(f"twist mode (fwd+aft vs port+stbd, bracket non-rigidity): {twist:+.3f} deg")
print(f"cross-check: mast pitch should appear in side-camera in-view tilts: "
      f"beta_port={brolls[2]:+.4f}, beta_stbd={brolls[3]:+.4f}")
print(f"cross-check: mast roll should appear in fwd/aft in-view tilts: "
      f"beta_fwd={brolls[0]:+.4f}, beta_aft={brolls[1]:+.4f}")

# --- parallax sweep for common mode c: el_true = el - alpha_cam - beta_cam*u + c
el_rel = el - alpha[cam] - brolls[cam]*u
cxm = x.mean(); cym = y.mean()
best = []
for c in np.arange(-1.0, 1.01, 0.05):
    e = el_rel + c
    m = e < -0.08                                 # need finite range
    Rr = h[m]/np.tan(np.radians(-e[m]))
    ok = Rr < 1500
    px = x[m][ok] + Rr[ok]*np.cos(np.radians(az[m][ok]))
    py = y[m][ok] + Rr[ok]*np.sin(np.radians(az[m][ok]))
    saz = np.floor(np.degrees(np.arctan2(py-cym, px-cxm))).astype(int)
    r = np.hypot(px-cxm, py-cym)
    cost_n = 0.0; wsum = 0
    for b in np.unique(saz):
        rr = r[saz==b]
        if len(rr) < 200: continue
        mad = np.median(np.abs(rr - np.median(rr)))
        cost_n += mad*len(rr); wsum += len(rr)
    frac_above = float((e > 0.02).mean())
    best.append((c, cost_n/max(wsum,1), frac_above, (~m).mean()))
arr = np.array(best)
i0 = arr[:,1].argmin()
print("\nparallax sweep (c, shore-scatter m, frac_above_horizon, frac_nearzero):")
for row in arr[::2]:
    mark = " <--" if row[0]==arr[i0,0] else ""
    print(f"  c={row[0]:+.2f}: scatter={row[1]:7.2f} m  above={100*row[2]:5.1f}%  nz={100*row[3]:4.1f}%{mark}")
print(f"\nbest common-mode c = {arr[i0,0]:+.2f} deg")
np.savez(f"{OUT}/solution.npz", alpha=alpha, beta=brolls, c=arr[i0,0], sweep=arr)
