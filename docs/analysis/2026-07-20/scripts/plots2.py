#!/usr/bin/env python3
"""Honest shore-consistency diagnostic: only rays with el < -0.2 deg (R < ~400 m),
scatter + shoreline, before vs after."""
import numpy as np, json, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R

import os
OUT = os.environ.get("CAMERA_CAL_WORKDIR", "/tmp/camera_mast_calibration")
CAMS = ["fwd", "aft", "port", "stbd"]
COLS = {"fwd":"tab:blue","aft":"tab:orange","port":"tab:green","stbd":"tab:red"}
sol = np.load(f"{OUT}/absolute_solution.npz")
alpha, beta = sol["alpha"], sol["beta"]
O = np.load(f"{OUT}/obs.npz")
cam = O["cam"].astype(int); el = O["el"]; az = O["az"]; u = np.degrees(O["u"])
x = O["x"]; y = O["y"]; h = O["h"]
keep = (el > -3.0) & (el < 1.6)
idx = np.where(keep)[0][::15]
cam, el, az, u, x, y, h = (a[idx] for a in (cam, el, az, u, x, y, h))

em = np.load(f"{OUT}/earth_map.npz"); Rem = R.from_quat(em["q"]); tem = em["t"]
def lla2ecef(lat, lon, hh):
    a=6378137.0; f=1/298.257223563; e2=f*(2-f)
    la=math.radians(lat); lo=math.radians(lon)
    N=a/math.sqrt(1-e2*math.sin(la)**2)
    return np.array([(N+hh)*math.cos(la)*math.cos(lo),(N+hh)*math.cos(la)*math.sin(lo),
                     (N*(1-e2)+hh)*math.sin(la)])
mass = json.load(open(f"{OUT}/massabesic.json"))["elements"][0]
rings = [np.array([Rem.inv().apply(lla2ecef(g["lat"],g["lon"],48.7)-tem)[:2] for g in m["geometry"]])
         for m in mass["members"] if m.get("geometry")]

fig, axes = plt.subplots(1, 2, figsize=(14.5, 7), sharex=True, sharey=True)
for ax, corrected in [(axes[0], False), (axes[1], True)]:
    e = (el - alpha[cam] - beta[cam]*u) if corrected else el.copy()
    m = e < -0.20
    Rr = h[m]/np.tan(np.radians(-e[m]))
    px = x[m] + Rr*np.cos(np.radians(az[m])); py = y[m] + Rr*np.sin(np.radians(az[m]))
    for ri in rings:
        ax.plot(ri[:,0], ri[:,1], "k-", lw=1.0, alpha=0.8)
    for ci, c in enumerate(CAMS):
        mm = cam[m]==ci
        ax.scatter(px[mm], py[mm], s=1.5, c=COLS[c], alpha=0.3, label=f"{c} (n={mm.sum()})")
    ax.plot(x, y, "m-", lw=1.5, label="boat track")
    ax.set_title(("AFTER correction" if corrected else "BEFORE (current URDF)") +
                 "  —  implied shore, rays steeper than -0.2°")
    ax.set_aspect("equal"); ax.legend(markerscale=8, loc="lower left", fontsize=8)
    ax.set_xlim(-650, 500); ax.set_ylim(-750, 350)
plt.tight_layout(); plt.savefig(f"{OUT}/shore_consistency2.png", dpi=110)
print("saved shore_consistency2.png")

# Per-camera elevation histograms, raw vs corrected (elevation_hist.png)
fig2, ax2 = plt.subplots(figsize=(9, 5))
for ci, c in enumerate(CAMS):
    m = cam == ci
    ax2.hist(el[m], bins=np.arange(-2.0, 1.2, 0.02), histtype="step",
             color=COLS[c], label=f"{c} (raw)", density=True)
    ax2.hist(el[m] - alpha[ci] - beta[ci]*u[m], bins=np.arange(-2.0, 1.2, 0.02),
             histtype="step", color=COLS[c], ls="--", alpha=0.6,
             label=f"{c} (corrected)", density=True)
ax2.axvline(0, color="k", lw=1)
ax2.annotate("physical limit\n(horizontal)", (0.02, 0.9),
             xycoords=("data", "axes fraction"), fontsize=8)
ax2.set_xlabel("waterline elevation in gravity frame [deg]")
ax2.set_ylabel("density")
ax2.set_title("Waterline elevation by camera — raw vs corrected")
ax2.legend(fontsize=7, ncol=2)
plt.tight_layout()
plt.savefig(f"{OUT}/elevation_hist.png", dpi=110)
print("saved elevation_hist.png")
